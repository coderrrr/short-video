"""
管理后台数据分析API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.models import get_db
from app.services.admin_analytics_service import AdminAnalyticsService
from app.schemas.admin_analytics_schemas import (
    ContentAnalyticsListResponse,
    ContentDetailedAnalytics,
    InteractionListResponse,
    CommentListResponse,
    ExportAnalyticsRequest
)
from app.utils.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/admin/analytics", tags=["admin-analytics"])


@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取仪表盘统计数据
    
    返回总体统计数据，包括总视频数、今日新增、点赞、收藏、评论等
    """
    from sqlalchemy import select, func, and_
    from datetime import datetime, timedelta
    from app.models import Content, Interaction, InteractionType, Comment, Share
    
    # 获取今天的开始时间
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 总视频数
    total_contents_result = await db.execute(
        select(func.count(Content.id))
    )
    total_contents = total_contents_result.scalar() or 0
    
    # 今日新增视频
    today_contents_result = await db.execute(
        select(func.count(Content.id))
        .where(Content.created_at >= today_start)
    )
    today_new_contents = today_contents_result.scalar() or 0
    
    # 总点赞数
    total_likes_result = await db.execute(
        select(func.count(Interaction.id))
        .where(Interaction.type == InteractionType.LIKE)
    )
    total_likes = total_likes_result.scalar() or 0
    
    # 今日点赞数
    today_likes_result = await db.execute(
        select(func.count(Interaction.id))
        .where(
            and_(
                Interaction.type == InteractionType.LIKE,
                Interaction.created_at >= today_start
            )
        )
    )
    today_likes = today_likes_result.scalar() or 0
    
    # 总收藏数
    total_favorites_result = await db.execute(
        select(func.count(Interaction.id))
        .where(Interaction.type == InteractionType.FAVORITE)
    )
    total_favorites = total_favorites_result.scalar() or 0
    
    # 今日收藏数
    today_favorites_result = await db.execute(
        select(func.count(Interaction.id))
        .where(
            and_(
                Interaction.type == InteractionType.FAVORITE,
                Interaction.created_at >= today_start
            )
        )
    )
    today_favorites = today_favorites_result.scalar() or 0
    
    # 总评论数
    total_comments_result = await db.execute(
        select(func.count(Comment.id))
    )
    total_comments = total_comments_result.scalar() or 0
    
    # 今日评论数
    today_comments_result = await db.execute(
        select(func.count(Comment.id))
        .where(Comment.created_at >= today_start)
    )
    today_comments = today_comments_result.scalar() or 0
    
    # 总用户数
    total_users_result = await db.execute(
        select(func.count(User.id))
    )
    total_users = total_users_result.scalar() or 0
    
    # KOL用户数
    total_kols_result = await db.execute(
        select(func.count(User.id))
        .where(User.is_kol == True)
    )
    total_kols = total_kols_result.scalar() or 0
    
    # 总观看次数
    total_views_result = await db.execute(
        select(func.sum(Content.view_count))
    )
    total_views = total_views_result.scalar() or 0
    
    # 总分享次数
    total_shares_result = await db.execute(
        select(func.count(Share.id))
    )
    total_shares = total_shares_result.scalar() or 0
    
    return {
        "total_contents": total_contents,
        "today_new_contents": today_new_contents,
        "total_likes": total_likes,
        "today_likes": today_likes,
        "total_favorites": total_favorites,
        "today_favorites": today_favorites,
        "total_comments": total_comments,
        "today_comments": today_comments,
        "total_users": total_users,
        "total_kols": total_kols,
        "total_views": total_views,
        "total_shares": total_shares
    }


@router.get("/top-contents")
async def get_top_contents(
    metric: str = Query("views", description="排序指标：views/likes/favorites"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取热门内容排行
    
    根据不同指标返回热门内容列表
    """
    from sqlalchemy import select, desc
    from sqlalchemy.orm import selectinload
    from app.models import Content, ContentStatus
    
    # 根据指标选择排序字段
    sort_field_map = {
        "views": Content.view_count,
        "likes": Content.like_count,
        "favorites": Content.favorite_count
    }
    
    sort_field = sort_field_map.get(metric, Content.view_count)
    
    # 查询热门内容
    result = await db.execute(
        select(Content)
        .options(selectinload(Content.creator))
        .where(Content.status == ContentStatus.PUBLISHED)
        .order_by(desc(sort_field))
        .limit(limit)
    )
    contents = result.scalars().all()
    
    # 构建响应
    items = []
    for content in contents:
        item = {
            "id": content.id,
            "title": content.title,
            "cover_url": content.cover_url,
            "view_count": content.view_count or 0,
            "like_count": content.like_count or 0,
            "favorite_count": content.favorite_count or 0,
            "created_at": content.created_at.isoformat() if content.created_at else None,
            "creator": None
        }
        
        if content.creator:
            item["creator"] = {
                "id": content.creator.id,
                "name": content.creator.name,
                "avatar_url": content.creator.avatar_url
            }
        
        items.append(item)
    
    return {"items": items}


@router.get("/top-users")
async def get_top_users(
    metric: str = Query("contents", description="排序指标：contents/likes/followers"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取活跃用户排行
    
    根据不同指标返回活跃用户列表
    """
    from sqlalchemy import select, func, desc
    from app.models import User, Content, Interaction, InteractionType, Follow
    
    if metric == "contents":
        # 按发布内容数排序
        result = await db.execute(
            select(
                User,
                func.count(Content.id).label("content_count")
            )
            .outerjoin(Content, Content.creator_id == User.id)
            .group_by(User.id)
            .order_by(desc("content_count"))
            .limit(limit)
        )
        users_data = result.all()
        
        items = []
        for user, content_count in users_data:
            items.append({
                "id": user.id,
                "name": user.name,
                "avatar_url": user.avatar_url,
                "department": user.department,
                "position": user.position,
                "is_kol": user.is_kol,
                "content_count": content_count or 0,
                "total_likes": 0,
                "followers_count": 0
            })
    
    elif metric == "likes":
        # 按获得点赞数排序
        result = await db.execute(
            select(
                User,
                func.count(Interaction.id).label("total_likes")
            )
            .join(Content, Content.creator_id == User.id)
            .outerjoin(
                Interaction,
                and_(
                    Interaction.content_id == Content.id,
                    Interaction.type == InteractionType.LIKE
                )
            )
            .group_by(User.id)
            .order_by(desc("total_likes"))
            .limit(limit)
        )
        users_data = result.all()
        
        items = []
        for user, total_likes in users_data:
            items.append({
                "id": user.id,
                "name": user.name,
                "avatar_url": user.avatar_url,
                "department": user.department,
                "position": user.position,
                "is_kol": user.is_kol,
                "content_count": 0,
                "total_likes": total_likes or 0,
                "followers_count": 0
            })
    
    else:  # followers
        # 按粉丝数排序
        result = await db.execute(
            select(
                User,
                func.count(Follow.id).label("followers_count")
            )
            .outerjoin(Follow, Follow.followee_id == User.id)
            .group_by(User.id)
            .order_by(desc("followers_count"))
            .limit(limit)
        )
        users_data = result.all()
        
        items = []
        for user, followers_count in users_data:
            items.append({
                "id": user.id,
                "name": user.name,
                "avatar_url": user.avatar_url,
                "department": user.department,
                "position": user.position,
                "is_kol": user.is_kol,
                "content_count": 0,
                "total_likes": 0,
                "followers_count": followers_count or 0
            })
    
    return {"items": items}


@router.get("/content/summary", response_model=ContentAnalyticsListResponse)
async def get_content_analytics(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_by: str = Query("view_count", description="排序字段"),
    order: str = Query("desc", description="排序方向：asc或desc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取内容分析汇总和列表
    
    需求：45.1
    
    返回内容性能指标列表，包括观看次数、完播次数、独立观众数、点赞数、收藏数等
    """
    service = AdminAnalyticsService(db)
    
    # 获取汇总数据
    summary = await service.get_content_analytics_summary()
    
    # 获取内容列表
    contents, total = await service.get_content_performance_list(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order
    )
    
    return ContentAnalyticsListResponse(
        summary=summary,
        contents=contents,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/content/{content_id}", response_model=ContentDetailedAnalytics)
async def get_content_detailed_analytics(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取特定内容的详细分析数据
    
    需求：45.2
    
    返回单个内容的详细性能指标，包括观看数据、互动数据、时间数据等
    """
    service = AdminAnalyticsService(db)
    analytics = await service.get_content_detailed_analytics(content_id)
    
    if not analytics:
        raise HTTPException(status_code=404, detail="内容不存在")
    
    return analytics


@router.post("/content/export")
async def export_analytics_report(
    request: ExportAnalyticsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    导出内容分析报告
    
    需求：45.4
    
    生成CSV或Excel格式的分析报告
    """
    service = AdminAnalyticsService(db)
    
    # 生成报告
    report_data = await service.export_analytics_report(
        content_ids=request.content_ids,
        format=request.format
    )
    
    # 设置响应头
    filename = f"content_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    if request.format == "excel":
        filename = filename.replace(".csv", ".xlsx")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        media_type = "text/csv"
    
    return Response(
        content=report_data,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/interactions/favorites", response_model=InteractionListResponse)
async def get_favorite_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: Optional[str] = Query(None, description="筛选用户ID"),
    content_id: Optional[str] = Query(None, description="筛选内容ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取收藏记录
    
    需求：49.1
    
    显示所有用户收藏记录及用户和内容信息
    """
    service = AdminAnalyticsService(db)
    records, total = await service.get_interaction_records(
        interaction_type="favorite",
        page=page,
        page_size=page_size,
        user_id=user_id,
        content_id=content_id
    )
    
    return InteractionListResponse(
        records=records,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/interactions/likes", response_model=InteractionListResponse)
async def get_like_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: Optional[str] = Query(None, description="筛选用户ID"),
    content_id: Optional[str] = Query(None, description="筛选内容ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取点赞记录
    
    需求：49.2
    
    显示所有用户点赞记录及用户和内容信息
    """
    service = AdminAnalyticsService(db)
    records, total = await service.get_interaction_records(
        interaction_type="like",
        page=page,
        page_size=page_size,
        user_id=user_id,
        content_id=content_id
    )
    
    return InteractionListResponse(
        records=records,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/interactions/bookmarks", response_model=InteractionListResponse)
async def get_bookmark_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: Optional[str] = Query(None, description="筛选用户ID"),
    content_id: Optional[str] = Query(None, description="筛选内容ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取标记记录
    
    需求：49.3
    
    显示所有用户标记记录包括笔记
    """
    service = AdminAnalyticsService(db)
    records, total = await service.get_interaction_records(
        interaction_type="bookmark",
        page=page,
        page_size=page_size,
        user_id=user_id,
        content_id=content_id
    )
    
    return InteractionListResponse(
        records=records,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/comments", response_model=CommentListResponse)
async def get_comment_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: Optional[str] = Query(None, description="筛选用户ID"),
    content_id: Optional[str] = Query(None, description="筛选内容ID"),
    search_text: Optional[str] = Query(None, description="搜索评论文本"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取评论记录
    
    需求：49.4
    
    显示所有用户评论及筛选和搜索功能
    """
    service = AdminAnalyticsService(db)
    comments, total = await service.get_comment_records(
        page=page,
        page_size=page_size,
        user_id=user_id,
        content_id=content_id,
        search_text=search_text
    )
    
    return CommentListResponse(
        comments=comments,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除评论
    
    需求：49.5
    
    管理员识别不当评论后可以删除
    """
    service = AdminAnalyticsService(db)
    success = await service.delete_comment(comment_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    return {"message": "评论已删除"}


# 导入datetime用于文件名
from datetime import datetime
