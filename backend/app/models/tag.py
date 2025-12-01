"""
标签模型
"""
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Tag(Base):
    """标签表"""
    __tablename__ = "tags"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 基本信息
    name = Column(String(50), nullable=False, comment="标签名称")
    category = Column(String(50), comment="标签分类（角色标签、主题标签、形式标签、质量标签、推荐标签）")
    
    # 层次结构
    parent_id = Column(String(36), ForeignKey("tags.id"), comment="父标签ID")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关系
    children = relationship("Tag", remote_side=[id])
    contents = relationship("ContentTag", back_populates="tag", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name}, category={self.category})>"
