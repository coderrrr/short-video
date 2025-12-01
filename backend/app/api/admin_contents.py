"""
管理后台内容管理API端点
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
import logging

from app.database import get_db

logger = logging.getLogger(__name__)
from app.schemas.content_schemas import (
    VideoMetadataCreate,
    ContentResponse,
    VideoUploadResponse,
    AdminContentFilterRequest,
    AdminContentListResponse,
    AdminBatchOperationRequest,
    AdminBatchOperationResponse,
    AdminBatchUploadResponse,
    AdminContentRemoveRequest,
    AdminFeatureContentRequest,
    AdminContentUploadRequest,
    AdminContentUpdateRequest
)
from app.services.content_service import ContentService
from app.utils.auth import get_current_user, require_admin
from app.models.user import User
from app.models.content import ContentStatus
import json

router = APIRouter(prefix="/admin/contents", tags=["admin-contents"])


def build_content_response(content) -> ContentResponse:
    """
    构建ContentResponse，包含创作者信息
    
    Args:
        content: Content模型对象
        
    Returns:
        ContentResponse对象
    """
    from sqlalchemy import inspect as sqlalchemy_inspect
    from sqlalchemy.orm.base import NEVER_SET
    
    # 获取精选相关字段
    is_featured = getattr(content, 'is_featured', 0)
    featured_priority = getattr(content, 'featured_priority', 0)
    featured_position = getattr(content, 'featured_position', None)
    
    content_dict = {
        "id": content.id,
        "title": content.title,
        "description": content.description,
        "video_url": content.video_url,
        "cover_url": content.cover_url,
        "duration": content.duration,
        "file_size": content.file_size,
        "creator_id": content.creator_id,
        "status": content.status,
        "content_type": content.content_type,
        "view_count": content.view_count,
        "like_count": content.like_count,
        "favorite_count": content.favorite_count,
        "comment_count": content.comment_count,
        "share_count": content.share_count,
        "created_at": content.created_at,
        "updated_at": content.updated_at,
        "published_at": content.published_at,
        "is_featured": is_featured,
        "featured_priority": featured_priority,
        "featured_position": featured_position,
        "priority": featured_priority,  # 前端兼容性：priority 是 featured_priority 的别名
    }
    
    # 添加创作者信息（如果已加载）
    try:
        # 检查creator关系是否已加载（不触发数据库查询）
        insp = sqlalchemy_inspect(content)
        creator_state = insp.attrs.creator
        
        # 检查是否已加载
        if creator_state.loaded_value is not NEVER_SET:
            creator = creator_state.loaded_value
            if isinstance(creator, dict):
                # 已经是字典格式
                content_dict["creator"] = creator
            elif creator is not None:
                # 将User对象转换为字典
                content_dict["creator"] = {
                    "id": creator.id,
                    "name": creator.name,
                    "employee_id": creator.employee_id,
                    "avatar_url": getattr(creator, 'avatar_url', None),
                    "department": getattr(creator, 'department', None),
                    "position": getattr(creator, 'position', None),
                    "is_kol": getattr(creator, 'is_kol', False)
                }
    except Exception as e:
        # 如果获取creator失败，记录日志但不影响主流程
        logger.warning(f"获取creator信息失败: {e}")
    
    return ContentResponse(**content_dict)


@router.get("/list", response_model=AdminContentListResponse)
async def list_all_contents(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="内容状态筛选"),
    content_type: Optional[str] = Query(None, description="内容类型筛选"),
    creator_id: Optional[str] = Query(None, description="创作者ID筛选"),
    search: Optional[str] = Query(None, description="搜索关键词（标题、描述）"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员查询所有内容列表（支持筛选和搜索）
    
    需求：38.1-38.4
    
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量（1-100）
    - **status**: 内容状态筛选（draft, under_review, approved, rejected, published, removed）
    - **content_type**: 内容类型筛选
    - **creator_id**: 创作者ID筛选
    - **search**: 搜索关键词（在标题和描述中搜索）
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    
    返回内容列表、总数和分页信息
    """
    content_service = ContentService(db)
    
    # 构建筛选条件
    filters = {}
    if status:
        filters['status'] = status
    if content_type:
        filters['content_type'] = content_type
    if creator_id:
        filters['creator_id'] = creator_id
    if start_date:
        filters['start_date'] = start_date
    if end_date:
        filters['end_date'] = end_date
    
    # 查询内容
    contents, total = await content_service.admin_list_contents(
        page=page,
        page_size=page_size,
        search=search,
        filters=filters
    )
    
    return AdminContentListResponse(
        items=[build_content_response(content) for content in contents],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/batch-operation", response_model=AdminBatchOperationResponse)
async def batch_operation(
    operation: AdminBatchOperationRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    批量操作内容
    
    需求：38.4
    
    - **operation_type**: 操作类型（approve, reject, remove, feature, unfeature）
    - **content_ids**: 内容ID列表
    - **reason**: 操作原因（拒绝时必填）
    
    返回操作结果
    """
    content_service = ContentService(db)
    
    # 执行批量操作
    result = await content_service.admin_batch_operation(
        operation_type=operation.operation_type,
        content_ids=operation.content_ids,
        admin_id=current_user.id,
        reason=operation.reason
    )
    
    return AdminBatchOperationResponse(
        success=result['success'],
        failed=result['failed'],
        total=len(operation.content_ids),
        message=f"批量操作完成：成功 {len(result['success'])} 个，失败 {len(result['failed'])} 个"
    )


@router.get("/{content_id}/detail", response_model=ContentResponse)
async def get_content_detail(
    content_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取内容详情（管理员视图）
    
    需求：38.1
    
    - **content_id**: 内容ID
    
    返回内容详细信息（包括AI分析结果、审核记录等）
    """
    content_service = ContentService(db)
    content = await content_service.admin_get_content_detail(content_id)
    
    if not content:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CONTENT_NOT_FOUND",
                "message": "内容不存在"
            }
        )
    
    return build_content_response(content)


@router.get("/statistics")
async def get_content_statistics(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取内容统计信息
    
    需求：38.1
    
    返回各状态内容数量、今日新增等统计数据
    """
    content_service = ContentService(db)
    stats = await content_service.admin_get_content_statistics()
    
    return stats



# ==================== 管理员内容创建 ====================

@router.post("", response_model=ContentResponse)
async def create_content(
    data: AdminContentUploadRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    创建内容记录（视频文件已通过 /admin/upload/video 上传）
    
    - **video_url**: 视频URL（已上传）
    - **cover_url**: 封面URL（可选，已上传）
    - **title**: 标题
    - **description**: 描述
    - **content_type**: 内容类型
    - **tag_ids**: 标签ID列表
    - **auto_publish**: 是否自动发布
    - **is_featured**: 是否精选
    - **priority**: 优先级
    """
    try:
        content_service = ContentService(db)
        
        # 创建内容
        content = await content_service.create_content_from_uploaded_file(
            admin_id=current_user.id,
            video_url=data.video_url,
            cover_url=data.cover_url,
            title=data.title,
            description=data.description,
            content_type=data.content_type,
            tag_ids=data.tag_ids,
            auto_publish=data.auto_publish,
            is_featured=data.is_featured,
            priority=data.priority
        )
        
        return build_content_response(content)
    except Exception as e:
        import traceback
        print(f"创建内容失败: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"创建内容失败: {str(e)}")


# ==================== 管理员内容上传（旧接口，保留兼容性）====================

@router.post("/upload", response_model=VideoUploadResponse)
async def admin_upload_video(
    file: UploadFile = File(..., description="视频文件"),
    metadata: str = Form(..., description="视频元数据（JSON格式）"),
    auto_publish: bool = Form(True, description="是否自动发布（跳过审核）"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员上传视频（支持自动发布）
    
    需求：39.1-39.4
    
    - **file**: 视频文件（MP4、MOV、AVI格式）
    - **metadata**: 视频元数据（JSON格式），包含title、description、content_type、tags
    - **auto_publish**: 是否自动发布（跳过审核，默认true）
    
    返回创建的内容ID和视频URL
    """
    # 解析元数据
    try:
        metadata_dict = json.loads(metadata)
        video_metadata = VideoMetadataCreate(**metadata_dict)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_METADATA",
                "message": "元数据格式错误，必须是有效的JSON"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_METADATA",
                "message": f"元数据验证失败: {str(e)}"
            }
        )
    
    # 上传视频
    content_service = ContentService(db)
    content = await content_service.admin_upload_video(
        file=file,
        admin_id=current_user.id,
        metadata=video_metadata,
        auto_publish=auto_publish
    )
    
    return VideoUploadResponse(
        content_id=content.id,
        video_url=content.video_url,
        status=content.status,
        message="视频上传成功" + ("并已自动发布" if auto_publish else "")
    )


@router.post("/batch-upload", response_model=AdminBatchUploadResponse)
async def admin_batch_upload_videos(
    files: List[UploadFile] = File(..., description="视频文件列表"),
    metadata_list: str = Form(..., description="视频元数据列表（JSON数组格式）"),
    auto_publish: bool = Form(True, description="是否自动发布（跳过审核）"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员批量上传视频
    
    需求：39.2
    
    - **files**: 视频文件列表
    - **metadata_list**: 视频元数据列表（JSON数组格式），每个元素包含title、description、content_type、tags
    - **auto_publish**: 是否自动发布（跳过审核，默认true）
    
    返回批量上传结果
    """
    # 解析元数据列表
    try:
        metadata_dicts = json.loads(metadata_list)
        if not isinstance(metadata_dicts, list):
            raise ValueError("元数据必须是数组格式")
        
        if len(metadata_dicts) != len(files):
            raise ValueError(f"元数据数量（{len(metadata_dicts)}）与文件数量（{len(files)}）不匹配")
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_METADATA",
                "message": "元数据格式错误，必须是有效的JSON数组"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_METADATA",
                "message": str(e)
            }
        )
    
    # 批量上传
    content_service = ContentService(db)
    success = []
    failed = []
    
    for i, (file, metadata_dict) in enumerate(zip(files, metadata_dicts)):
        try:
            # 验证元数据
            video_metadata = VideoMetadataCreate(**metadata_dict)
            
            # 上传视频
            content = await content_service.admin_upload_video(
                file=file,
                admin_id=current_user.id,
                metadata=video_metadata,
                auto_publish=auto_publish
            )
            
            success.append({
                'index': i,
                'filename': file.filename,
                'content_id': content.id,
                'video_url': content.video_url,
                'status': content.status
            })
            
        except Exception as e:
            logger.error(f"批量上传失败: index={i}, filename={file.filename}, error={str(e)}")
            failed.append({
                'index': i,
                'filename': file.filename,
                'reason': str(e)
            })
    
    return AdminBatchUploadResponse(
        success=success,
        failed=failed,
        total=len(files),
        message=f"批量上传完成：成功 {len(success)} 个，失败 {len(failed)} 个"
    )



# ==================== 管理员内容删除和管理 ====================

@router.post("/{content_id}/remove", response_model=ContentResponse)
async def admin_remove_content(
    content_id: str,
    request: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员下架单个内容
    
    需求：40.1-40.4
    
    - **content_id**: 内容ID
    - **reason**: 下架原因（JSON body）
    
    返回下架后的内容信息
    """
    content_service = ContentService(db)
    
    reason = request.get('reason', '管理员下架')
    
    try:
        content = await content_service.admin_remove_content(
            content_id=content_id,
            admin_id=current_user.id,
            reason=reason,
            create_audit_log=True
        )
        
        return build_content_response(content)
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CONTENT_NOT_FOUND",
                "message": str(e)
            }
        )


@router.post("/batch-remove", response_model=AdminBatchOperationResponse)
async def admin_batch_remove_contents(
    request: AdminContentRemoveRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员批量下架内容
    
    需求：40.2
    
    - **content_ids**: 内容ID列表
    - **reason**: 下架原因
    - **create_audit_log**: 是否创建审计日志
    
    返回批量操作结果
    """
    content_service = ContentService(db)
    
    success = []
    failed = []
    
    for content_id in request.content_ids:
        try:
            await content_service.admin_remove_content(
                content_id=content_id,
                admin_id=current_user.id,
                reason=request.reason,
                create_audit_log=request.create_audit_log
            )
            success.append(content_id)
            
        except Exception as e:
            logger.error(f"批量下架失败: content_id={content_id}, error={str(e)}")
            failed.append({
                'content_id': content_id,
                'reason': str(e)
            })
    
    return AdminBatchOperationResponse(
        success=success,
        failed=failed,
        total=len(request.content_ids),
        message=f"批量下架完成：成功 {len(success)} 个，失败 {len(failed)} 个"
    )


@router.post("/batch-delete", response_model=AdminBatchOperationResponse)
async def admin_batch_delete_contents(
    request: AdminContentRemoveRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员批量删除内容（物理删除）
    
    - **content_ids**: 内容ID列表
    - **reason**: 删除原因
    - **create_audit_log**: 是否创建审计日志（删除操作会忽略此参数）
    
    注意：此操作会永久删除内容，无法恢复
    
    返回批量操作结果
    """
    content_service = ContentService(db)
    
    success = []
    failed = []
    
    for content_id in request.content_ids:
        try:
            await content_service.admin_delete_content(
                content_id=content_id,
                admin_id=current_user.id
            )
            success.append(content_id)
            
        except Exception as e:
            logger.error(f"批量删除失败: content_id={content_id}, error={str(e)}")
            failed.append({
                'content_id': content_id,
                'reason': str(e)
            })
    
    return AdminBatchOperationResponse(
        success=success,
        failed=failed,
        total=len(request.content_ids),
        message=f"批量删除完成：成功 {len(success)} 个，失败 {len(failed)} 个"
    )


@router.get("/{content_id}/audit-logs")
async def get_content_audit_logs(
    content_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取内容的审计日志
    
    需求：40.4
    
    - **content_id**: 内容ID
    
    返回审计日志列表
    """
    content_service = ContentService(db)
    
    try:
        logs = await content_service.get_content_audit_logs(content_id)
        
        return {
            "content_id": content_id,
            "logs": [
                {
                    "id": log.id,
                    "reviewer_id": log.reviewer_id,
                    "review_type": log.review_type,
                    "status": log.status,
                    "reason": log.reason,
                    "created_at": log.created_at
                }
                for log in logs
            ]
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CONTENT_NOT_FOUND",
                "message": str(e)
            }
        )


@router.post("/{content_id}/restore", response_model=ContentResponse)
async def admin_restore_content(
    content_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员恢复已下架的内容
    
    需求：40.1
    
    - **content_id**: 内容ID
    
    返回恢复后的内容信息
    """
    content_service = ContentService(db)
    
    try:
        content = await content_service.admin_restore_content(
            content_id=content_id,
            admin_id=current_user.id
        )
        
        return build_content_response(content)
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CONTENT_NOT_FOUND",
                "message": str(e)
            }
        )



# ==================== 管理员精选内容推广 ====================

@router.post("/{content_id}/feature", response_model=ContentResponse)
async def admin_feature_content(
    content_id: str,
    request: AdminFeatureContentRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员设置精选内容
    
    需求：41.1-41.4
    
    - **content_id**: 内容ID
    - **is_featured**: 是否精选
    - **priority**: 显示优先级（1-100，数字越大优先级越高）
    - **featured_position**: 精选位置（homepage, category_top等）
    
    返回更新后的内容信息
    """
    content_service = ContentService(db)
    
    try:
        content = await content_service.admin_feature_content(
            content_id=content_id,
            is_featured=request.is_featured,
            priority=request.priority,
            featured_position=request.featured_position
        )
        
        return build_content_response(content)
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_OPERATION",
                "message": str(e)
            }
        )


@router.get("/featured/list")
async def list_featured_contents(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    featured_position: Optional[str] = Query(None, description="精选位置筛选"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取精选内容列表
    
    需求：41.2
    
    - **page**: 页码
    - **page_size**: 每页数量
    - **featured_position**: 精选位置筛选
    
    返回精选内容列表（按优先级排序）
    """
    content_service = ContentService(db)
    
    contents, total = await content_service.list_featured_contents(
        page=page,
        page_size=page_size,
        featured_position=featured_position
    )
    
    return {
        "items": [build_content_response(content) for content in contents],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.post("/{content_id}/update-priority")
async def update_featured_priority(
    content_id: str,
    priority: int = Form(..., ge=1, le=100, description="显示优先级（1-100）"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    更新精选内容的显示优先级
    
    需求：41.3
    
    - **content_id**: 内容ID
    - **priority**: 显示优先级（1-100，数字越大优先级越高）
    
    返回更新结果
    """
    content_service = ContentService(db)
    
    try:
        content = await content_service.update_featured_priority(
            content_id=content_id,
            priority=priority
        )
        
        return {
            "success": True,
            "content_id": content_id,
            "priority": priority,
            "message": "优先级更新成功"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_OPERATION",
                "message": str(e)
            }
        )


@router.post("/batch-feature", response_model=AdminBatchOperationResponse)
async def batch_feature_contents(
    content_ids: List[str] = Form(..., description="内容ID列表"),
    is_featured: bool = Form(..., description="是否精选"),
    priority: Optional[int] = Form(None, ge=1, le=100, description="显示优先级"),
    featured_position: Optional[str] = Form(None, description="精选位置"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    批量设置精选内容
    
    需求：41.1
    
    - **content_ids**: 内容ID列表
    - **is_featured**: 是否精选
    - **priority**: 显示优先级
    - **featured_position**: 精选位置
    
    返回批量操作结果
    """
    content_service = ContentService(db)
    
    success = []
    failed = []
    
    for content_id in content_ids:
        try:
            await content_service.admin_feature_content(
                content_id=content_id,
                is_featured=is_featured,
                priority=priority,
                featured_position=featured_position
            )
            success.append(content_id)
            
        except Exception as e:
            logger.error(f"批量设置精选失败: content_id={content_id}, error={str(e)}")
            failed.append({
                'content_id': content_id,
                'reason': str(e)
            })
    
    return AdminBatchOperationResponse(
        success=success,
        failed=failed,
        total=len(content_ids),
        message=f"批量设置精选完成：成功 {len(success)} 个，失败 {len(failed)} 个"
    )


# ==================== 专家审核管理 ====================

@router.get("/expert-review", response_model=AdminContentListResponse)
async def list_expert_review_contents(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    review_status: Optional[str] = Query(None, description="审核状态筛选"),
    expert_id: Optional[str] = Query(None, description="专家ID筛选"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取需要专家审核的内容列表
    
    - **page**: 页码
    - **page_size**: 每页数量
    - **review_status**: 审核状态（pending_assign, in_review, approved, rejected）
    - **expert_id**: 专家ID
    """
    content_service = ContentService(db)
    
    # 构建筛选条件
    filters = {}
    if review_status:
        filters['expert_review_status'] = review_status
    if expert_id:
        filters['expert_id'] = expert_id
    
    # 查询需要专家审核的内容
    contents, total = await content_service.admin_list_contents(
        page=page,
        page_size=page_size,
        search=None,
        filters=filters
    )
    
    return AdminContentListResponse(
        items=[build_content_response(content) for content in contents],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/expert-review/statistics")
async def get_expert_review_statistics(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取专家审核统计信息
    
    返回待分配、审核中、已完成的数量
    
    注：当前为简化实现，返回基于review_records表的统计
    """
    from sqlalchemy import select, func
    from app.models.review_record import ReviewRecord
    
    # 统计专家审核记录
    # 审核中
    in_review_result = await db.execute(
        select(func.count(ReviewRecord.id)).where(
            ReviewRecord.review_type == 'expert_review',
            ReviewRecord.status == 'pending'
        )
    )
    in_review = in_review_result.scalar() or 0
    
    # 已完成（已批准或已拒绝）
    completed_result = await db.execute(
        select(func.count(ReviewRecord.id)).where(
            ReviewRecord.review_type == 'expert_review',
            ReviewRecord.status.in_(['approved', 'rejected'])
        )
    )
    completed = completed_result.scalar() or 0
    
    # 待分配：暂时返回0，需要后续实现专家审核分配功能
    pending_assign = 0
    
    return {
        'pending_assign': pending_assign,
        'in_review': in_review,
        'completed': completed
    }


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    data: AdminContentUpdateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    更新内容信息
    
    - **content_id**: 内容ID
    - **title**: 标题（可选）
    - **description**: 描述（可选）
    - **content_type**: 内容类型（可选）
    - **tag_ids**: 标签ID列表（可选）
    - **is_featured**: 是否精选（可选）
    - **priority**: 优先级（可选）
    - **video_url**: 视频URL（可选）
    - **cover_url**: 封面URL（可选）
    
    返回更新后的内容信息
    """
    try:
        content_service = ContentService(db)
        
        # 更新内容
        content = await content_service.admin_update_content(
            content_id=content_id,
            admin_id=current_user.id,
            title=data.title,
            description=data.description,
            content_type=data.content_type,
            tag_ids=data.tag_ids,
            video_url=data.video_url,
            cover_url=data.cover_url,
            is_featured=data.is_featured,
            priority=data.priority
        )
        
        return build_content_response(content)
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CONTENT_NOT_FOUND",
                "message": str(e)
            }
        )
    except Exception as e:
        import traceback
        print(f"更新内容失败: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"更新内容失败: {str(e)}")


@router.delete("/{content_id}")
async def delete_content(
    content_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    删除内容（物理删除）
    
    - **content_id**: 内容ID
    
    注意：此操作会永久删除内容，无法恢复
    """
    content_service = ContentService(db)
    
    try:
        await content_service.admin_delete_content(content_id, current_user.id)
        return {"message": "内容删除成功", "content_id": content_id}
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CONTENT_NOT_FOUND",
                "message": str(e)
            }
        )
