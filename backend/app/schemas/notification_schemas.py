"""
通知相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    """通知类型"""
    REVIEW_STATUS = "review_status"
    INTERACTION = "interaction"
    MENTION = "mention"
    FOLLOW = "follow"
    LEARNING_REMINDER = "learning_reminder"
    SYSTEM = "system"


class NotificationBase(BaseModel):
    """通知基础模型"""
    type: NotificationType = Field(..., description="通知类型")
    title: str = Field(..., max_length=200, description="通知标题")
    content: str = Field(..., description="通知内容")
    related_content_id: Optional[str] = Field(None, description="关联的内容ID")
    related_user_id: Optional[str] = Field(None, description="关联的用户ID")
    related_comment_id: Optional[str] = Field(None, description="关联的评论ID")


class NotificationCreate(NotificationBase):
    """创建通知请求"""
    user_id: str = Field(..., description="接收通知的用户ID")


class NotificationResponse(NotificationBase):
    """通知响应"""
    id: str = Field(..., description="通知ID")
    user_id: str = Field(..., description="用户ID")
    is_read: bool = Field(..., description="是否已读")
    created_at: datetime = Field(..., description="创建时间")
    read_at: Optional[datetime] = Field(None, description="阅读时间")
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """通知列表响应"""
    notifications: list[NotificationResponse] = Field(..., description="通知列表")
    total: int = Field(..., description="总数")
    unread_count: int = Field(..., description="未读数量")


class MarkAsReadRequest(BaseModel):
    """标记为已读请求"""
    notification_ids: list[str] = Field(..., description="通知ID列表")


class NotificationSettingsBase(BaseModel):
    """通知设置基础模型"""
    enable_review_notifications: bool = Field(True, description="启用审核通知")
    enable_interaction_notifications: bool = Field(True, description="启用互动通知")
    enable_mention_notifications: bool = Field(True, description="启用@提及通知")
    enable_follow_notifications: bool = Field(True, description="启用关注通知")
    enable_learning_reminders: bool = Field(True, description="启用学习提醒")
    enable_system_notifications: bool = Field(True, description="启用系统通知")


class NotificationSettingsUpdate(NotificationSettingsBase):
    """更新通知设置请求"""
    pass


class NotificationSettingsResponse(NotificationSettingsBase):
    """通知设置响应"""
    id: str = Field(..., description="设置ID")
    user_id: str = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class CacheInfoResponse(BaseModel):
    """缓存信息响应"""
    total_size_bytes: int = Field(..., description="总大小（字节）")
    total_size_mb: float = Field(..., description="总大小（MB）")
    video_count: int = Field(..., description="视频数量")
    videos: list[dict] = Field(..., description="视频列表")


class ClearCacheRequest(BaseModel):
    """清除缓存请求"""
    confirm: bool = Field(..., description="确认清除")
