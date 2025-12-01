"""
播放进度模型
用于跟踪用户的视频播放进度
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class PlaybackProgress(Base):
    """播放进度表"""
    __tablename__ = "playback_progress"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 外键
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="用户ID")
    content_id = Column(String(36), ForeignKey("contents.id"), nullable=False, comment="内容ID")
    
    # 播放进度
    progress_seconds = Column(Float, default=0.0, nullable=False, comment="播放进度（秒）")
    duration_seconds = Column(Float, nullable=False, comment="视频总时长（秒）")
    progress_percentage = Column(Float, default=0.0, nullable=False, comment="播放进度百分比")
    
    # 播放速度
    playback_speed = Column(Float, default=1.0, nullable=False, comment="播放速度")
    
    # 播放状态
    is_completed = Column(Integer, default=0, nullable=False, comment="是否完成（0=未完成，1=已完成）")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    last_played_at = Column(DateTime, default=datetime.utcnow, comment="最后播放时间")
    
    # 关系
    user = relationship("User", backref="playback_progress")
    content = relationship("Content", backref="playback_progress")
    
    def __repr__(self):
        return f"<PlaybackProgress(id={self.id}, user_id={self.user_id}, content_id={self.content_id}, progress={self.progress_percentage}%)>"


# 创建索引
Index('idx_playback_user', PlaybackProgress.user_id)
Index('idx_playback_content', PlaybackProgress.content_id)
Index('idx_playback_user_content', PlaybackProgress.user_id, PlaybackProgress.content_id, unique=True)
Index('idx_playback_last_played', PlaybackProgress.last_played_at.desc())
