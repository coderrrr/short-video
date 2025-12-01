"""
通知设置模型
用于存储用户的通知偏好设置
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class NotificationSettings(Base):
    """通知设置表"""
    __tablename__ = "notification_settings"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 外键
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    
    # 通知开关
    enable_review_notifications = Column(Boolean, default=True, nullable=False, comment="启用审核通知")
    enable_interaction_notifications = Column(Boolean, default=True, nullable=False, comment="启用互动通知")
    enable_mention_notifications = Column(Boolean, default=True, nullable=False, comment="启用@提及通知")
    enable_follow_notifications = Column(Boolean, default=True, nullable=False, comment="启用关注通知")
    enable_learning_reminders = Column(Boolean, default=True, nullable=False, comment="启用学习提醒")
    enable_system_notifications = Column(Boolean, default=True, nullable=False, comment="启用系统通知")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    user = relationship("User", backref="notification_settings")
    
    def __repr__(self):
        return f"<NotificationSettings(id={self.id}, user_id={self.user_id})>"
