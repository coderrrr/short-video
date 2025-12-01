"""
推荐结果缓存模型
用于缓存用户的推荐内容，提高推荐性能
"""
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class RecommendationCache(Base):
    """推荐结果缓存表"""
    __tablename__ = "recommendation_caches"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 外键
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    
    # 缓存数据
    # 推荐内容ID列表 ["content_id1", "content_id2", ...]
    content_ids = Column(JSON, nullable=False, comment="推荐内容ID列表")
    
    # 缓存元数据
    page = Column(Integer, default=1, comment="页码")
    page_size = Column(Integer, default=20, comment="每页数量")
    
    # 缓存有效期
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    user = relationship("User", backref="recommendation_caches")
    
    def __repr__(self):
        return f"<RecommendationCache(id={self.id}, user_id={self.user_id}, page={self.page})>"
    
    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        return datetime.utcnow() > self.expires_at
