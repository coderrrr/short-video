"""
内容标签关联模型
"""
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class ContentTag(Base):
    """内容标签关联表"""
    __tablename__ = "content_tags"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 外键
    content_id = Column(String(36), ForeignKey("contents.id"), nullable=False, comment="内容ID")
    tag_id = Column(String(36), ForeignKey("tags.id"), nullable=False, comment="标签ID")
    
    # AI匹配信息
    confidence = Column(Float, comment="AI匹配的置信度")
    is_auto = Column(Boolean, default=True, comment="是否AI自动匹配")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关系
    content = relationship("Content", back_populates="tags")
    tag = relationship("Tag", back_populates="contents")
    
    def __repr__(self):
        return f"<ContentTag(content_id={self.content_id}, tag_id={self.tag_id}, confidence={self.confidence})>"


# 创建索引
Index('idx_content_tag_content', ContentTag.content_id)
Index('idx_content_tag_tag', ContentTag.tag_id)
