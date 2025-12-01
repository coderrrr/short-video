"""
用户偏好模型
用于存储用户的内容偏好，支持个性化推荐
"""
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class UserPreference(Base):
    """用户偏好表"""
    __tablename__ = "user_preferences"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 外键
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    
    # 偏好数据
    # 角色标签偏好 {"tag_id": weight}
    role_tag_weights = Column(JSON, default=dict, comment="角色标签权重")
    
    # 主题标签偏好 {"tag_id": weight}
    topic_tag_weights = Column(JSON, default=dict, comment="主题标签权重")
    
    # 内容类型偏好 {"content_type": weight}
    content_type_weights = Column(JSON, default=dict, comment="内容类型权重")
    
    # 创作者偏好 {"creator_id": weight}
    creator_weights = Column(JSON, default=dict, comment="创作者权重")
    
    # 观看历史统计
    total_watch_count = Column(Float, default=0.0, comment="总观看次数")
    total_watch_duration = Column(Float, default=0.0, comment="总观看时长（秒）")
    
    # 互动统计
    total_like_count = Column(Float, default=0.0, comment="总点赞次数")
    total_favorite_count = Column(Float, default=0.0, comment="总收藏次数")
    total_comment_count = Column(Float, default=0.0, comment="总评论次数")
    total_share_count = Column(Float, default=0.0, comment="总分享次数")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    user = relationship("User", backref="preference")
    
    def __repr__(self):
        return f"<UserPreference(id={self.id}, user_id={self.user_id})>"
