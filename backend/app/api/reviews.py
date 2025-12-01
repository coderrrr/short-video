"""
管理后台审核管理API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.database import get_db
from app.schemas.content_schemas import (
    ReviewQueueResponse,
    ContentApproveRequest,
    ContentRejectRequest,
    BatchReviewRequest,
    BatchReviewResponse,
    ContentReviewDetailResponse,
    ContentResponse
)
from app.services.content_service import ContentService
from app.utils.auth import get_current_user, require_admin
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/reviews", tags=["admin-reviews"])


def build_content_response(content) -> ContentResponse:
    """
    构建ContentResponse，包含创作者信息
    
    Args:
        content: Content模型对象
        
    Returns:
        ContentResponse对象
    """
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


@router.get("/queue", response_model=ReviewQueueResponse)
async def get_review_queue(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    content_type: Optional[str] = Query(None, description="内容类型筛选"),
    creator_id: Optional[str] = Query(None, description="创作者ID筛选"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取审核队列（所有状态为"审核中"的内容）
    
    需求：42.1, 42.2
    
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量（1-100）
    - **content_type**: 内容类型筛选
    - **creator_id**: 创作者ID筛选
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    
    返回待审核内容列表、总数和分页信息
    """
    content_service = ContentService(db)
    
    # 构建筛选条件
    filters = {
        'status': 'under_review'  # 只查询审核中的内容
    }
    if content_type:
        filters['content_type'] = content_type
    if creator_id:
        filters['creator_id'] = creator_id
    if start_date:
        filters['start_date'] = start_date
    if end_date:
        filters['end_date'] = end_date
    
    # 查询审核队列
    contents, total = await content_service.admin_list_contents(
        page=page,
        page_size=page_size,
        search=None,
        filters=filters
    )
    
    return ReviewQueueResponse(
        items=[build_content_response(content) for content in contents],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/{content_id}/detail", response_model=ContentReviewDetailResponse)
async def get_content_review_detail(
    content_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取内容审核详情（包括审核记录和AI分析结果）
    
    需求：42.2
    
    - **content_id**: 内容ID
    
    返回内容详细信息、审核记录和AI分析结果
    """
    content_service = ContentService(db)
    
    try:
        detail = await content_service.get_content_review_detail(content_id)
        
        return ContentReviewDetailResponse(
            content=ContentResponse.model_validate(detail['content']),
            review_records=detail['review_records']
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CONTENT_NOT_FOUND",
                "message": str(e)
            }
        )


@router.post("/approve", response_model=ContentResponse)
async def approve_content(
    request: ContentApproveRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    批准内容（将状态从"审核中"改为"已发布"）
    
    需求：42.3
    
    - **content_id**: 内容ID
    - **comment**: 审核备注（可选）
    
    返回批准后的内容信息
    """
    content_service = ContentService(db)
    
    try:
        content = await content_service.approve_content(
            content_id=request.content_id,
            reviewer_id=current_user.id,
            comment=request.comment
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


@router.post("/reject", response_model=ContentResponse)
async def reject_content(
    request: ContentRejectRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    拒绝内容（将状态从"审核中"改为"已驳回"）
    
    需求：42.4
    
    - **content_id**: 内容ID
    - **reason**: 拒绝原因（必填）
    
    返回拒绝后的内容信息
    """
    content_service = ContentService(db)
    
    try:
        content = await content_service.reject_content(
            content_id=request.content_id,
            reviewer_id=current_user.id,
            reason=request.reason
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


@router.post("/batch", response_model=BatchReviewResponse)
async def batch_review(
    request: BatchReviewRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    批量审核内容（批准或拒绝）
    
    需求：42.5
    
    - **content_ids**: 内容ID列表
    - **action**: 操作类型（approve或reject）
    - **reason**: 拒绝原因（action为reject时必填）
    
    返回批量操作结果
    """
    content_service = ContentService(db)
    
    success = []
    failed = []
    
    for content_id in request.content_ids:
        try:
            if request.action == 'approve':
                await content_service.approve_content(
                    content_id=content_id,
                    reviewer_id=current_user.id,
                    comment=None
                )
            else:  # reject
                await content_service.reject_content(
                    content_id=content_id,
                    reviewer_id=current_user.id,
                    reason=request.reason
                )
            
            success.append(content_id)
            
        except Exception as e:
            logger.error(f"批量审核失败: content_id={content_id}, action={request.action}, error={str(e)}")
            failed.append({
                'content_id': content_id,
                'reason': str(e)
            })
    
    action_text = "批准" if request.action == 'approve' else "拒绝"
    return BatchReviewResponse(
        success=success,
        failed=failed,
        total=len(request.content_ids),
        message=f"批量{action_text}完成：成功 {len(success)} 个，失败 {len(failed)} 个"
    )


@router.get("/statistics")
async def get_review_statistics(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取审核统计信息
    
    需求：42.1
    
    返回待审核数量、今日审核数量等统计数据
    """
    content_service = ContentService(db)
    stats = await content_service.get_review_statistics()
    
    return stats
