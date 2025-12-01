"""
通知服务
处理通知的创建、查询、标记已读等功能
"""
import uuid
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Notification,
    NotificationSettings,
    NotificationType,
    User,
)
from app.schemas.notification_schemas import (
    NotificationCreate,
    NotificationSettingsUpdate,
)


class NotificationService:
    """通知服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        content: str,
        related_content_id: Optional[str] = None,
        related_user_id: Optional[str] = None,
        related_comment_id: Optional[str] = None,
    ) -> Notification:
        """
        创建通知
        
        Args:
            user_id: 接收通知的用户ID
            notification_type: 通知类型
            title: 通知标题
            content: 通知内容
            related_content_id: 关联的内容ID
            related_user_id: 关联的用户ID
            related_comment_id: 关联的评论ID
            
        Returns:
            创建的通知对象
        """
        # 检查用户的通知设置
        settings = await self.get_notification_settings(user_id)
        if not self._should_send_notification(settings, notification_type):
            # 用户已禁用此类型的通知
            return None
        
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=notification_type,
            title=title,
            content=content,
            related_content_id=related_content_id,
            related_user_id=related_user_id,
            related_comment_id=related_comment_id,
            is_read=False,
        )
        
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        
        # TODO: 集成AWS SNS发送推送通知
        # await self._send_push_notification(notification)
        
        return notification
    
    def _should_send_notification(
        self,
        settings: NotificationSettings,
        notification_type: NotificationType
    ) -> bool:
        """检查是否应该发送通知"""
        if not settings:
            return True  # 默认发送
        
        type_to_setting = {
            NotificationType.REVIEW_STATUS: settings.enable_review_notifications,
            NotificationType.INTERACTION: settings.enable_interaction_notifications,
            NotificationType.MENTION: settings.enable_mention_notifications,
            NotificationType.FOLLOW: settings.enable_follow_notifications,
            NotificationType.LEARNING_REMINDER: settings.enable_learning_reminders,
            NotificationType.SYSTEM: settings.enable_system_notifications,
        }
        
        return type_to_setting.get(notification_type, True)
    
    async def get_notifications(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
    ) -> Tuple[List[Notification], int, int]:
        """
        获取用户的通知列表
        
        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的记录数
            unread_only: 是否只返回未读通知
            
        Returns:
            (通知列表, 总数, 未读数量)
        """
        # 构建查询条件
        conditions = [Notification.user_id == user_id]
        if unread_only:
            conditions.append(Notification.is_read == False)
        
        # 查询通知列表
        query = (
            select(Notification)
            .where(and_(*conditions))
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        notifications = result.scalars().all()
        
        # 查询总数
        count_query = select(func.count(Notification.id)).where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 查询未读数量
        unread_query = select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        unread_result = await self.db.execute(unread_query)
        unread_count = unread_result.scalar()
        
        return notifications, total, unread_count
    
    async def mark_as_read(
        self,
        user_id: str,
        notification_ids: List[str]
    ) -> int:
        """
        标记通知为已读
        
        Args:
            user_id: 用户ID
            notification_ids: 通知ID列表
            
        Returns:
            标记的通知数量
        """
        # 查询未读通知
        query = select(Notification).where(
            and_(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        result = await self.db.execute(query)
        notifications = result.scalars().all()
        
        # 标记为已读
        count = 0
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            count += 1
        
        await self.db.commit()
        return count
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """
        标记所有通知为已读
        
        Args:
            user_id: 用户ID
            
        Returns:
            标记的通知数量
        """
        # 查询所有未读通知
        query = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        result = await self.db.execute(query)
        notifications = result.scalars().all()
        
        # 标记为已读
        count = 0
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            count += 1
        
        await self.db.commit()
        return count
    
    async def get_notification_settings(
        self,
        user_id: str
    ) -> Optional[NotificationSettings]:
        """
        获取用户的通知设置
        
        Args:
            user_id: 用户ID
            
        Returns:
            通知设置对象，如果不存在则返回None
        """
        query = select(NotificationSettings).where(
            NotificationSettings.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_or_update_notification_settings(
        self,
        user_id: str,
        settings_data: NotificationSettingsUpdate
    ) -> NotificationSettings:
        """
        创建或更新通知设置
        
        Args:
            user_id: 用户ID
            settings_data: 设置数据
            
        Returns:
            通知设置对象
        """
        # 查询现有设置
        settings = await self.get_notification_settings(user_id)
        
        if settings:
            # 更新现有设置
            for key, value in settings_data.model_dump().items():
                setattr(settings, key, value)
            settings.updated_at = datetime.utcnow()
        else:
            # 创建新设置
            settings = NotificationSettings(
                id=str(uuid.uuid4()),
                user_id=user_id,
                **settings_data.model_dump()
            )
            self.db.add(settings)
        
        await self.db.commit()
        await self.db.refresh(settings)
        return settings
    
    async def send_review_status_notification(
        self,
        user_id: str,
        content_id: str,
        content_title: str,
        status: str,
        reason: Optional[str] = None
    ):
        """
        发送审核状态通知
        
        Args:
            user_id: 创作者用户ID
            content_id: 内容ID
            content_title: 内容标题
            status: 审核状态
            reason: 拒绝原因（如果被拒绝）
        """
        if status == "approved":
            title = "内容审核通过"
            content = f"您的内容《{content_title}》已通过审核，现已发布"
        elif status == "rejected":
            title = "内容审核未通过"
            content = f"您的内容《{content_title}》未通过审核"
            if reason:
                content += f"，原因：{reason}"
        else:
            title = "内容审核状态更新"
            content = f"您的内容《{content_title}》的审核状态已更新为：{status}"
        
        await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.REVIEW_STATUS,
            title=title,
            content=content,
            related_content_id=content_id
        )
    
    async def send_interaction_notification(
        self,
        user_id: str,
        actor_id: str,
        actor_name: str,
        content_id: str,
        content_title: str,
        interaction_type: str
    ):
        """
        发送互动通知
        
        Args:
            user_id: 内容创作者用户ID
            actor_id: 互动者用户ID
            actor_name: 互动者姓名
            content_id: 内容ID
            content_title: 内容标题
            interaction_type: 互动类型（like, comment, share）
        """
        type_to_text = {
            "like": "点赞了",
            "comment": "评论了",
            "share": "分享了"
        }
        
        action_text = type_to_text.get(interaction_type, "互动了")
        title = f"{actor_name}{action_text}您的内容"
        content = f"{actor_name}{action_text}您的内容《{content_title}》"
        
        await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.INTERACTION,
            title=title,
            content=content,
            related_content_id=content_id,
            related_user_id=actor_id
        )
    
    async def send_mention_notification(
        self,
        user_id: str,
        actor_id: str,
        actor_name: str,
        content_id: str,
        content_title: str,
        comment_id: str
    ):
        """
        发送@提及通知
        
        Args:
            user_id: 被提及的用户ID
            actor_id: 提及者用户ID
            actor_name: 提及者姓名
            content_id: 内容ID
            content_title: 内容标题
            comment_id: 评论ID
        """
        title = f"{actor_name}在评论中提到了您"
        content = f"{actor_name}在《{content_title}》的评论中提到了您"
        
        await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.MENTION,
            title=title,
            content=content,
            related_content_id=content_id,
            related_user_id=actor_id,
            related_comment_id=comment_id
        )
    
    async def send_follow_notification(
        self,
        user_id: str,
        follower_id: str,
        follower_name: str
    ):
        """
        发送关注通知
        
        Args:
            user_id: 被关注的用户ID
            follower_id: 关注者用户ID
            follower_name: 关注者姓名
        """
        title = f"{follower_name}关注了您"
        content = f"{follower_name}开始关注您了"
        
        await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.FOLLOW,
            title=title,
            content=content,
            related_user_id=follower_id
        )
