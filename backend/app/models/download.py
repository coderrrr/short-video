"""
下载记录模型
用于跟踪用户的视频下载记录
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Download(Base):
    """下载记录表"""
    __tablename__ = "downloads"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 外键
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="用户ID")
    content_id = Column(String(36), ForeignKey("contents.id"), nullable=False, comment="内容ID")
    
    # 下载信息
    file_size = Column(Float, nullable=False, comment="文件大小（字节）")
    download_progress = Column(Float, default=0.0, nullable=False, comment="下载进度（0-100）")
    download_status = Column(String(20), default="pending", nullable=False, comment="下载状态：pending, downloading, completed, failed")
    local_path = Column(String(500), comment="本地存储路径")
    quality = Column(String(20), default="hd", nullable=False, comment="下载质量：hd, sd")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    # 关系
    user = relationship("User", backref="downloads")
    content = relationship("Content", backref="downloads")
    
    def __repr__(self):
        return f"<Download(id={self.id}, user_id={self.user_id}, content_id={self.content_id}, status={self.download_status})>"


# 创建索引
Index('idx_download_user', Download.user_id)
Index('idx_download_content', Download.content_id)
Index('idx_download_user_content', Download.user_id, Download.content_id)
Index('idx_download_status', Download.download_status)
Index('idx_download_created', Download.created_at.desc())
