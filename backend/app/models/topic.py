"""
专题模型
"""
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


# 专题内容关联表
topic_contents = Table(
    'topic_contents',
    Base.metadata,
    Column('topic_id', String(36), ForeignKey('topics.id', ondelete='CASCADE'), primary_key=True),
    Column('content_id', String(36), ForeignKey('contents.id', ondelete='CASCADE'), primary_key=True),
    Column('order', Integer, default=0),  # 内容在专题中的排序
    Column('created_at', DateTime, default=datetime.utcnow)
)


class Topic(Base):
    """专题模型 - 主题分组的内容集合"""
    __tablename__ = "topics"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False, comment="专题名称")
    description = Column(Text, comment="专题描述")
    cover_url = Column(String(500), comment="专题封面图片URL")
    
    # 创建者
    creator_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # 状态
    is_active = Column(Integer, default=1, comment="是否激活：1-激活，0-停用")
    
    # 统计数据
    content_count = Column(Integer, default=0, comment="内容数量")
    view_count = Column(Integer, default=0, comment="浏览次数")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    creator = relationship("User", backref="created_topics")
    contents = relationship(
        "Content",
        secondary=topic_contents,
        backref="topics",
        order_by="topic_contents.c.order"
    )
    
    def __repr__(self):
        return f"<Topic {self.name}>"
