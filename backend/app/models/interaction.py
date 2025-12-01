"""
互动记录模型
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from .base import Base


class InteractionType(str, Enum):
    """互动类型枚举"""
    LIKE = "LIKE"  # 点赞
    FAVORITE = "FAVORITE"  # 收藏
    BOOKMARK = "BOOKMARK"  # 标记
    COMMENT = "COMMENT"  # 评论
    SHARE = "SHARE"  # 分享


class Interaction(Base):
    """互动记录表"""
    __tablename__ = "interactions"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 外键
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="用户ID")
    content_id = Column(String(36), ForeignKey("contents.id"), nullable=False, comment="内容ID")
    
    # 互动类型
    type = Column(SQLEnum(InteractionType), nullable=False, comment="互动类型")
    
    # 针对bookmark的额外字段
    note = Column(Text, comment="标记笔记")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关系
    user = relationship("User", back_populates="interactions")
    content = relationship("Content", back_populates="interactions")
    
    def __repr__(self):
        return f"<Interaction(id={self.id}, user_id={self.user_id}, content_id={self.content_id}, type={self.type})>"


# 创建索引
Index('idx_interaction_user', Interaction.user_id)
Index('idx_interaction_content', Interaction.content_id)
Index('idx_interaction_type', Interaction.type)
Index('idx_user_content_type', Interaction.user_id, Interaction.content_id, Interaction.type)
