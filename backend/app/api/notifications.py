"""
通知相关的API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.models import get_db, User
from app.services.notification_service import NotificationService
from app.schemas.notification_schemas import (
    NotificationListResponse,
    NotificationResponse,
    MarkAsReadRequest,
    NotificationSettingsUpdate,
    NotificationSettingsResponse,
    CacheInfoResponse,
    ClearCacheRequest,
)
from app.utils.auth import get_current_user
from app.services.download_service import DownloadService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    unread_only: bool = Query(False, description="是否只返回未读通知"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的通知列表
    
    - **skip**: 跳过的记录数（分页）
    - **limit**: 返回的记录数（分页）
    - **unread_only**: 是否只返回未读通知
    """
    service = NotificationService(db)
    notifications, total, unread_count = await service.get_notifications(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )
    
    return NotificationListResponse(
        notifications=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        unread_count=unread_count
    )


@router.post("/mark-as-read")
async def mark_notifications_as_read(
    request: MarkAsReadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    标记通知为已读
    
    - **notification_ids**: 要标记为已读的通知ID列表
    """
    service = NotificationService(db)
    count = await service.mark_as_read(
        user_id=current_user.id,
        notification_ids=request.notification_ids
    )
    
    return {
        "message": f"成功标记{count}条通知为已读",
        "count": count
    }


@router.post("/mark-all-as-read")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    标记所有通知为已读
    """
    service = NotificationService(db)
    count = await service.mark_all_as_read(user_id=current_user.id)
    
    return {
        "message": f"成功标记{count}条通知为已读",
        "count": count
    }


@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的通知设置
    """
    service = NotificationService(db)
    settings = await service.get_notification_settings(user_id=current_user.id)
    
    if not settings:
        # 如果没有设置，返回默认设置
        settings = await service.create_or_update_notification_settings(
            user_id=current_user.id,
            settings_data=NotificationSettingsUpdate()
        )
    
    return NotificationSettingsResponse.model_validate(settings)


@router.put("/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    settings_data: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前用户的通知设置
    
    - **enable_review_notifications**: 启用审核通知
    - **enable_interaction_notifications**: 启用互动通知
    - **enable_mention_notifications**: 启用@提及通知
    - **enable_follow_notifications**: 启用关注通知
    - **enable_learning_reminders**: 启用学习提醒
    - **enable_system_notifications**: 启用系统通知
    """
    service = NotificationService(db)
    settings = await service.create_or_update_notification_settings(
        user_id=current_user.id,
        settings_data=settings_data
    )
    
    return NotificationSettingsResponse.model_validate(settings)


@router.get("/cache/info", response_model=CacheInfoResponse)
async def get_cache_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取缓存信息（已下载的视频）
    """
    service = DownloadService(db)
    downloads = await service.get_user_downloads(user_id=current_user.id)
    
    total_size_bytes = sum(d.file_size or 0 for d in downloads)
    total_size_mb = total_size_bytes / (1024 * 1024)
    
    videos = [
        {
            "id": d.id,
            "content_id": d.content_id,
            "file_size": d.file_size,
            "downloaded_at": d.downloaded_at.isoformat() if d.downloaded_at else None
        }
        for d in downloads
    ]
    
    return CacheInfoResponse(
        total_size_bytes=total_size_bytes,
        total_size_mb=round(total_size_mb, 2),
        video_count=len(downloads),
        videos=videos
    )


@router.post("/cache/clear")
async def clear_cache(
    request: ClearCacheRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    清除缓存（删除所有已下载的视频）
    
    - **confirm**: 必须为true才能执行清除操作
    """
    if not request.confirm:
        raise HTTPException(
            status_code=400,
            detail="必须确认清除缓存操作"
        )
    
    service = DownloadService(db)
    count = await service.clear_user_downloads(user_id=current_user.id)
    
    return {
        "message": f"成功清除{count}个缓存视频",
        "count": count
    }
