"""
关注关系模型
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Follow(Base):
    """关注关系表"""
    __tablename__ = "follows"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 外键
    follower_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="关注者ID")
    followee_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="被关注者ID")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关系
    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    followee = relationship("User", foreign_keys=[followee_id], back_populates="followers")
    
    def __repr__(self):
        return f"<Follow(id={self.id}, follower_id={self.follower_id}, followee_id={self.followee_id})>"


# 创建索引
Index('idx_follow_follower', Follow.follower_id)
Index('idx_follow_followee', Follow.followee_id)
Index('idx_follow_unique', Follow.follower_id, Follow.followee_id, unique=True)
