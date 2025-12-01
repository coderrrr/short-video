"""
分享记录模型
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Share(Base):
    """分享记录表"""
    __tablename__ = "shares"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 外键
    content_id = Column(String(36), ForeignKey("contents.id"), nullable=False, comment="内容ID")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="分享用户ID")
    
    # 分享信息
    platform = Column(String(50), nullable=False, comment="分享平台（wechat/link）")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="分享时间")
    
    # 关系
    content = relationship("Content", back_populates="shares")
    user = relationship("User", back_populates="shares")
    
    def __repr__(self):
        return f"<Share(id={self.id}, user_id={self.user_id}, content_id={self.content_id})>"


# 创建索引
Index('idx_share_content', Share.content_id)
Index('idx_share_user', Share.user_id)
Index('idx_share_created', Share.created_at.desc())
