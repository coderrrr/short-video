"""
内容相关的API端点
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

from app.database import get_db
from app.schemas.content_schemas import (
    VideoMetadataCreate,
    VideoMetadataUpdate,
    VideoUploadResponse,
    ContentResponse,
    CoverImageUploadResponse,
    VideoFrameExtractRequest,
    VideoEditRequest,
    ContentFilterRequest
)
from app.services.content_service import ContentService
from app.services.video_editor import VideoEditor
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.content import ContentStatus
import json

router = APIRouter(prefix="/contents", tags=["contents"])


def build_content_response(content, is_liked=False, is_favorited=False, is_bookmarked=False) -> ContentResponse:
    """
    构建ContentResponse，包含创作者信息
    
    Args:
        content: Content模型对象
        is_liked: 是否已点赞
        is_favorited: 是否已收藏
        is_bookmarked: 是否已标记
        
    Returns:
        ContentResponse对象
    """
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
        "is_liked": is_liked,
        "is_favorited": is_favorited,
        "is_bookmarked": is_bookmarked,
    }
    
    # 添加创作者信息（如果已加载）
    if hasattr(content, 'creator') and content.creator:
        content_dict["creator"] = {
            "id": content.creator.id,
            "name": content.creator.name,
            "employee_id": content.creator.employee_id,
            "avatar_url": content.creator.avatar_url,
            "department": content.creator.department,
            "position": content.creator.position,
            "is_kol": content.creator.is_kol
        }
    
    return ContentResponse(**content_dict)


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(..., description="视频文件"),
    metadata: str = Form(..., description="视频元数据（JSON格式）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传视频
    
    - **file**: 视频文件（MP4、MOV、AVI格式）
    - **metadata**: 视频元数据（JSON格式），包含title、description、content_type、tags
    
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
    content = await content_service.upload_video(
        file=file,
        user_id=current_user.id,
        metadata=video_metadata
    )
    
    return VideoUploadResponse(
        content_id=content.id,
        video_url=content.video_url,
        status=content.status,
        message="视频上传成功"
    )


@router.put("/{content_id}/metadata", response_model=ContentResponse)
async def update_content_metadata(
    content_id: str,
    metadata: VideoMetadataUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新视频元数据
    
    - **content_id**: 内容ID
    - **metadata**: 更新的元数据
    
    返回更新后的内容信息
    """
    content_service = ContentService(db)
    content = await content_service.update_metadata(
        content_id=content_id,
        user_id=current_user.id,
        metadata=metadata
    )
    
    return build_content_response(content)


@router.post("/{content_id}/cover", response_model=CoverImageUploadResponse)
async def upload_cover_image(
    content_id: str,
    file: UploadFile = File(..., description="封面图片文件"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传封面图片
    
    - **content_id**: 内容ID
    - **file**: 封面图片文件（JPEG、PNG格式）
    
    返回封面图片URL
    """
    content_service = ContentService(db)
    cover_url = await content_service.upload_cover_image(
        content_id=content_id,
        user_id=current_user.id,
        file=file
    )
    
    return CoverImageUploadResponse(
        cover_url=cover_url,
        message="封面图片上传成功"
    )


@router.post("/{content_id}/frames", response_model=List[str])
async def extract_video_frames(
    content_id: str,
    request: VideoFrameExtractRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    提取视频帧
    
    - **content_id**: 内容ID
    - **interval**: 提取间隔（秒）
    
    返回视频帧URL列表
    """
    content_service = ContentService(db)
    frames = await content_service.extract_video_frames(
        content_id=content_id,
        user_id=current_user.id,
        interval=request.interval
    )
    
    return frames


# ==================== 个性化推荐 ====================

@router.get("/recommended")
async def get_recommended_contents(
    page: int = 1,
    page_size: int = 20,
    exclude_viewed: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取个性化推荐内容
    
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量
    - **exclude_viewed**: 是否排除已观看内容（默认true）
    
    返回推荐内容列表
    
    推荐算法考虑：
    - 用户角色标签
    - 观看历史
    - 互动模式（点赞、收藏、评论、分享）
    - 内容时效性
    - 内容热度
    """
    from app.services.recommendation_service import RecommendationService
    
    from sqlalchemy.orm import selectinload
    
    recommendation_service = RecommendationService(db)
    contents = await recommendation_service.get_recommended_content(
        user_id=current_user.id,
        page=page,
        size=page_size,
        exclude_viewed=exclude_viewed
    )
    
    # 构建响应，包含创作者信息
    content_responses = [build_content_response(content) for content in contents]
    
    return {
        "contents": content_responses,
        "total": len(contents),
        "page": page,
        "page_size": page_size
    }


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取内容详情
    
    - **content_id**: 内容ID
    
    返回内容详细信息（包含当前用户的互动状态）
    """
    from sqlalchemy import select, and_
    from app.models.interaction import Interaction, InteractionType
    
    content_service = ContentService(db)
    content = await content_service.get_content(content_id)
    
    if not content:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CONTENT_NOT_FOUND",
                "message": "内容不存在"
            }
        )
    
    # 查询用户的互动状态
    interactions_result = await db.execute(
        select(Interaction.type).where(
            and_(
                Interaction.user_id == current_user.id,
                Interaction.content_id == content_id
            )
        )
    )
    interaction_types = {row[0] for row in interactions_result.fetchall()}
    
    # 构建响应，包含创作者信息和互动状态
    return build_content_response(
        content,
        is_liked=InteractionType.LIKE in interaction_types,
        is_favorited=InteractionType.FAVORITE in interaction_types,
        is_bookmarked=InteractionType.BOOKMARK in interaction_types
    )



@router.post("/{content_id}/edit/trim", response_model=ContentResponse)
async def trim_video(
    content_id: str,
    edit_request: VideoEditRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    裁剪视频
    
    - **content_id**: 内容ID
    - **start_time**: 开始时间（秒）
    - **end_time**: 结束时间（秒）
    
    返回更新后的内容信息
    """
    content_service = ContentService(db)
    content = await content_service.get_content(content_id)
    
    if not content:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CONTENT_NOT_FOUND",
                "message": "内容不存在"
            }
        )
    
    if content.creator_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "无权限编辑此内容"
            }
        )
    
    # 裁剪视频
    video_editor = VideoEditor()
    output_key = f"videos/{content_id}_trimmed.mp4"
    
    try:
        new_video_url = await video_editor.trim_video(
            input_url=content.video_url,
            start_time=edit_request.start_time,
            end_time=edit_request.end_time,
            output_key=output_key
        )
        
        # 更新内容记录
        content.video_url = new_video_url
        content.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(content)
        
        return build_content_response(content)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "VIDEO_EDIT_FAILED",
                "message": f"视频裁剪失败: {str(e)}"
            }
        )


@router.post("/{content_id}/edit/volume", response_model=ContentResponse)
async def adjust_video_volume(
    content_id: str,
    edit_request: VideoEditRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    调节视频音量
    
    - **content_id**: 内容ID
    - **volume**: 音量倍数（0-2）
    
    返回更新后的内容信息
    """
    content_service = ContentService(db)
    content = await content_service.get_content(content_id)
    
    if not content:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CONTENT_NOT_FOUND",
                "message": "内容不存在"
            }
        )
    
    if content.creator_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "无权限编辑此内容"
            }
        )
    
    # 调节音量
    video_editor = VideoEditor()
    output_key = f"videos/{content_id}_volume.mp4"
    
    try:
        new_video_url = await video_editor.adjust_volume(
            input_url=content.video_url,
            volume=edit_request.volume,
            output_key=output_key
        )
        
        # 更新内容记录
        content.video_url = new_video_url
        content.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(content)
        
        return build_content_response(content)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "VIDEO_EDIT_FAILED",
                "message": f"音量调节失败: {str(e)}"
            }
        )


@router.get("/{content_id}/info")
async def get_video_info(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频信息（用于实时预览）
    
    - **content_id**: 内容ID
    
    返回视频信息（时长、分辨率等）
    """
    content_service = ContentService(db)
    content = await content_service.get_content(content_id)
    
    if not content:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CONTENT_NOT_FOUND",
                "message": "内容不存在"
            }
        )
    
    if content.creator_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "无权限访问此内容"
            }
        )
    
    # 获取视频信息
    video_editor = VideoEditor()
    
    try:
        info = await video_editor.get_video_info(content.video_url)
        return info
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "VIDEO_INFO_FAILED",
                "message": f"获取视频信息失败: {str(e)}"
            }
        )


# ==================== 草稿管理 ====================

@router.post("/{content_id}/save-draft", response_model=ContentResponse)
async def save_draft(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    保存草稿
    
    - **content_id**: 内容ID
    
    返回保存的草稿信息
    """
    content_service = ContentService(db)
    content = await content_service.save_draft(
        content_id=content_id,
        user_id=current_user.id
    )
    
    return build_content_response(content)


@router.get("/{content_id}/load-draft", response_model=ContentResponse)
async def load_draft(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    加载草稿
    
    - **content_id**: 内容ID
    
    返回草稿详细信息
    """
    content_service = ContentService(db)
    content = await content_service.load_draft(
        content_id=content_id,
        user_id=current_user.id
    )
    
    return build_content_response(content)


@router.get("/drafts/list")
async def list_drafts(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查询草稿列表
    
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量
    
    返回草稿列表和总数
    """
    content_service = ContentService(db)
    drafts, total = await content_service.list_drafts(
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )
    
    return {
        "drafts": [build_content_response(draft) for draft in drafts],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.delete("/{content_id}/draft")
async def delete_draft(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除草稿
    
    - **content_id**: 内容ID
    
    返回删除结果
    """
    content_service = ContentService(db)
    success = await content_service.delete_draft(
        content_id=content_id,
        user_id=current_user.id
    )
    
    return {
        "success": success,
        "message": "草稿删除成功"
    }


# ==================== 内容审核 ====================

@router.post("/{content_id}/submit", response_model=ContentResponse)
async def submit_for_review(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    提交内容进行审核
    
    - **content_id**: 内容ID
    
    返回提交的内容信息
    """
    content_service = ContentService(db)
    content = await content_service.submit_for_review(
        content_id=content_id,
        user_id=current_user.id
    )
    
    return build_content_response(content)


@router.post("/{content_id}/approve", response_model=ContentResponse)
async def approve_content(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批准内容
    
    - **content_id**: 内容ID
    
    返回批准的内容信息
    
    注意：此接口需要管理员权限
    """
    # TODO: 验证管理员权限
    
    content_service = ContentService(db)
    content = await content_service.approve_content(
        content_id=content_id,
        reviewer_id=current_user.id
    )
    
    return build_content_response(content)


@router.post("/{content_id}/reject", response_model=ContentResponse)
async def reject_content(
    content_id: str,
    reason: str = Form(..., description="拒绝原因"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    拒绝内容
    
    - **content_id**: 内容ID
    - **reason**: 拒绝原因
    
    返回拒绝的内容信息
    
    注意：此接口需要管理员权限
    """
    # TODO: 验证管理员权限
    
    content_service = ContentService(db)
    content = await content_service.reject_content(
        content_id=content_id,
        reviewer_id=current_user.id,
        reason=reason
    )
    
    return build_content_response(content)


@router.get("/review/queue")
async def get_review_queue(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取审核队列
    
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量
    
    返回待审核内容列表和总数
    
    注意：此接口需要管理员权限
    """
    # TODO: 验证管理员权限
    
    content_service = ContentService(db)
    contents, total = await content_service.get_review_queue(
        page=page,
        page_size=page_size
    )
    
    return {
        "contents": [build_content_response(content) for content in contents],
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ==================== 专家审核 ====================

@router.post("/{content_id}/expert-review/assign", response_model=ContentResponse)
async def assign_expert_review(
    content_id: str,
    expert_id: str = Form(..., description="专家ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    分配专家审核
    
    - **content_id**: 内容ID
    - **expert_id**: 专家ID
    
    返回内容信息
    
    注意：此接口需要管理员权限
    """
    # TODO: 验证管理员权限
    
    content_service = ContentService(db)
    content = await content_service.assign_expert_review(
        content_id=content_id,
        expert_id=expert_id,
        assigner_id=current_user.id
    )
    
    return build_content_response(content)


@router.post("/{content_id}/expert-review/approve", response_model=ContentResponse)
async def expert_approve_content(
    content_id: str,
    feedback: str = Form(None, description="专家反馈（可选）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    专家批准内容
    
    - **content_id**: 内容ID
    - **feedback**: 专家反馈（可选）
    
    返回批准的内容信息
    
    注意：此接口需要专家权限
    """
    # TODO: 验证专家权限
    
    content_service = ContentService(db)
    content = await content_service.expert_approve_content(
        content_id=content_id,
        expert_id=current_user.id,
        feedback=feedback
    )
    
    return build_content_response(content)


@router.post("/{content_id}/expert-review/reject", response_model=ContentResponse)
async def expert_reject_content(
    content_id: str,
    feedback: str = Form(..., description="专家反馈"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    专家拒绝内容
    
    - **content_id**: 内容ID
    - **feedback**: 专家反馈
    
    返回拒绝的内容信息
    
    注意：此接口需要专家权限
    """
    # TODO: 验证专家权限
    
    content_service = ContentService(db)
    content = await content_service.expert_reject_content(
        content_id=content_id,
        expert_id=current_user.id,
        feedback=feedback
    )
    
    return build_content_response(content)


# ==================== 分类浏览 ====================

@router.get("/categories/list")
async def list_categories(
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有活动的内容分类
    
    返回分类列表（包含层次结构）
    """
    content_service = ContentService(db)
    categories = await content_service.list_categories()
    
    return {
        "categories": [
            {
                "id": cat.id,
                "name": cat.name,
                "category": cat.category,
                "parent_id": cat.parent_id
            }
            for cat in categories
        ]
    }


@router.get("/categories/{category_id}")
async def get_category_hierarchy(
    category_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取分类的层次结构（包括子分类）
    
    - **category_id**: 分类ID
    
    返回分类对象（包含子分类）
    """
    content_service = ContentService(db)
    category = await content_service.get_category_hierarchy(category_id)
    
    if not category:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CATEGORY_NOT_FOUND",
                "message": "分类不存在"
            }
        )
    
    # 递归构建子分类树
    def build_category_tree(cat):
        return {
            "id": cat.id,
            "name": cat.name,
            "category": cat.category,
            "parent_id": cat.parent_id,
            "children": [build_category_tree(child) for child in cat.children]
        }
    
    return build_category_tree(category)


@router.get("/categories/{category_id}/contents")
async def list_contents_by_category(
    category_id: str,
    page: int = 1,
    page_size: int = 20,
    include_subcategories: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    按分类查询内容
    
    - **category_id**: 分类ID
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量
    - **include_subcategories**: 是否包含子分类的内容（默认true）
    
    返回内容列表和总数
    """
    content_service = ContentService(db)
    contents, total = await content_service.list_contents_by_category(
        category_id=category_id,
        page=page,
        page_size=page_size,
        include_subcategories=include_subcategories
    )
    
    return {
        "contents": [build_content_response(content) for content in contents],
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ==================== 内容搜索 ====================

@router.get("/search")
async def search_contents(
    q: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    搜索内容（全文搜索：标题、描述、标签）
    
    - **q**: 搜索关键词（多个关键词用空格分隔，使用OR逻辑）
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量
    
    返回内容列表和总数
    """
    content_service = ContentService(db)
    contents, total = await content_service.search_contents(
        query=q,
        page=page,
        page_size=page_size
    )
    
    # 如果没有结果，返回空结果提示
    if total == 0:
        return {
            "contents": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "message": "未找到匹配的内容"
        }
    
    return {
        "contents": [build_content_response(content) for content in contents],
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ==================== 多维内容筛选 ====================

@router.post("/filter")
async def filter_contents(
    filter_request: ContentFilterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    多维内容筛选（使用AND逻辑）
    
    - **content_type**: 内容类型列表（可选）
    - **position**: 岗位列表（可选）
    - **skill**: 技能列表（可选）
    - **tags**: 标签列表（可选）
    - **creator_id**: 创作者ID（可选）
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量
    
    返回内容列表和总数
    """
    content_service = ContentService(db)
    contents, total = await content_service.filter_contents(
        content_type=filter_request.content_type,
        position=filter_request.position,
        skill=filter_request.skill,
        tags=filter_request.tags,
        creator_id=filter_request.creator_id,
        page=filter_request.page,
        page_size=filter_request.page_size
    )
    
    # 如果没有结果，返回空结果提示
    if total == 0:
        return {
            "contents": [],
            "total": 0,
            "page": filter_request.page,
            "page_size": filter_request.page_size,
            "message": "未找到匹配的内容"
        }
    
    return {
        "contents": [build_content_response(content) for content in contents],
        "total": total,
        "page": filter_request.page,
        "page_size": filter_request.page_size
    }


@router.post("/{content_id}/track-view")
async def track_content_view(
    content_id: str,
    watch_duration: float = Form(..., description="观看时长（秒）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    记录内容观看行为（用于更新用户偏好）
    
    - **content_id**: 内容ID
    - **watch_duration**: 观看时长（秒）
    
    返回成功消息
    """
    from app.services.recommendation_service import RecommendationService
    
    recommendation_service = RecommendationService(db)
    await recommendation_service.update_preference_from_view(
        user_id=current_user.id,
        content_id=content_id,
        watch_duration=watch_duration
    )
    
    return {
        "success": True,
        "message": "观看记录已更新"
    }


@router.post("/{content_id}/track-interaction")
async def track_content_interaction(
    content_id: str,
    interaction_type: str = Form(..., description="互动类型（like/favorite/comment/share）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    记录内容互动行为（用于更新用户偏好）
    
    - **content_id**: 内容ID
    - **interaction_type**: 互动类型（like/favorite/comment/share）
    
    返回成功消息
    

    """
    from app.services.recommendation_service import RecommendationService
    from app.models.interaction import InteractionType
    
    # 验证互动类型
    try:
        interaction_enum = InteractionType(interaction_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_INTERACTION_TYPE",
                "message": f"无效的互动类型: {interaction_type}"
            }
        )
    
    recommendation_service = RecommendationService(db)
    
    # 更新用户偏好
    await recommendation_service.update_preference_from_interaction(
        user_id=current_user.id,
        content_id=content_id,
        interaction_type=interaction_enum
    )
    
    return {
        "success": True,
        "message": "互动记录已更新"
    }


# ==================== 内容发布管理 ====================

@router.get("/me/published")
async def get_my_published_contents(
    status: str = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的发布内容列表（我的发布）
    
    - **status**: 内容状态筛选（draft, under_review, approved, rejected, published, removed）
    - **page**: 页码
    - **page_size**: 每页数量
    
    返回内容列表和分页信息
    """
    content_service = ContentService(db)
    contents, total = await content_service.get_user_contents(
        user_id=current_user.id,
        status=status,
        page=page,
        page_size=page_size
    )
    
    return {
        "items": [build_content_response(content) for content in contents],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.post("/{content_id}/resubmit", response_model=ContentResponse)
async def resubmit_content(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    重新提交被驳回的内容或草稿
    
    - **content_id**: 内容ID
    
    返回更新后的内容信息
    """
    content_service = ContentService(db)
    
    try:
        content = await content_service.resubmit_content(content_id, current_user.id)
        return build_content_response(content)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
