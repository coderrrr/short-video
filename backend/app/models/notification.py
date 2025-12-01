"""
通知模型
用于存储系统通知
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from .base import Base


class NotificationType(str, Enum):
    """通知类型"""
    REVIEW_STATUS = "review_status"  # 审核状态通知
    INTERACTION = "interaction"  # 互动通知（点赞、评论、分享）
    MENTION = "mention"  # @提及通知
    FOLLOW = "follow"  # 关注通知
    LEARNING_REMINDER = "learning_reminder"  # 学习提醒
    SYSTEM = "system"  # 系统通知


class Notification(Base):
    """通知表"""
    __tablename__ = "notifications"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 外键
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="接收通知的用户ID")
    
    # 通知内容
    type = Column(SQLEnum(NotificationType), nullable=False, comment="通知类型")
    title = Column(String(200), nullable=False, comment="通知标题")
    content = Column(Text, nullable=False, comment="通知内容")
    
    # 关联数据
    related_content_id = Column(String(36), comment="关联的内容ID")
    related_user_id = Column(String(36), comment="关联的用户ID（如点赞者、评论者）")
    related_comment_id = Column(String(36), comment="关联的评论ID")
    
    # 状态
    is_read = Column(Boolean, default=False, nullable=False, comment="是否已读")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    read_at = Column(DateTime, comment="阅读时间")
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, user_id={self.user_id}, is_read={self.is_read})>"
