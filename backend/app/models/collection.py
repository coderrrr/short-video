"""
合集模型
"""
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


# 合集内容关联表
collection_contents = Table(
    'collection_contents',
    Base.metadata,
    Column('collection_id', String(36), ForeignKey('collections.id', ondelete='CASCADE'), primary_key=True),
    Column('content_id', String(36), ForeignKey('contents.id', ondelete='CASCADE'), primary_key=True),
    Column('order', Integer, nullable=False, comment="内容在合集中的顺序"),
    Column('created_at', DateTime, default=datetime.utcnow)
)


class Collection(Base):
    """合集模型 - 结构化学习序列的内容集合"""
    __tablename__ = "collections"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False, comment="合集名称")
    description = Column(Text, comment="合集描述")
    cover_url = Column(String(500), comment="合集封面图片URL")
    
    # 创建者
    creator_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # 状态
    is_active = Column(Integer, default=1, comment="是否激活：1-激活，0-停用")
    
    # 统计数据
    content_count = Column(Integer, default=0, comment="内容数量")
    view_count = Column(Integer, default=0, comment="浏览次数")
    completion_count = Column(Integer, default=0, comment="完成次数")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    creator = relationship("User", backref="created_collections")
    contents = relationship(
        "Content",
        secondary=collection_contents,
        backref="collections",
        order_by="collection_contents.c.order"
    )
    
    def __repr__(self):
        return f"<Collection {self.name}>"
