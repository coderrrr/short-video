"""
视频质量偏好模型
用于存储用户的视频质量设置
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class VideoQualityPreference(Base):
    """视频质量偏好表"""
    __tablename__ = "video_quality_preferences"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 外键
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    
    # 质量设置
    quality = Column(String(20), default="auto", nullable=False, comment="视频质量：auto, hd, sd")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    user = relationship("User", backref="video_quality_preference")
    
    def __repr__(self):
        return f"<VideoQualityPreference(id={self.id}, user_id={self.user_id}, quality={self.quality})>"


# 创建索引
Index('idx_video_quality_user', VideoQualityPreference.user_id, unique=True)
