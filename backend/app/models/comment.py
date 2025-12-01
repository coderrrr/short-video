"""
评论模型
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Comment(Base):
    """评论表"""
    __tablename__ = "comments"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 外键
    content_id = Column(String(36), ForeignKey("contents.id"), nullable=False, comment="内容ID")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="用户ID")
    parent_id = Column(String(36), ForeignKey("comments.id"), comment="父评论ID（回复评论）")
    
    # 评论内容
    text = Column(Text, nullable=False, comment="评论文本")
    
    # @提及的用户
    mentioned_users = Column(JSON, comment='提及的用户ID列表 ["user_id1", "user_id2"]')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关系
    content = relationship("Content", back_populates="comments")
    user = relationship("User", back_populates="comments")
    # 自引用关系：一个评论可以有多个回复
    # 使用backref而不是relationship来避免delete-orphan问题
    replies = relationship(
        "Comment",
        backref="parent",
        remote_side=[id],
        cascade="all, delete",  # 移除delete-orphan
        single_parent=True  # 确保每个回复只有一个父评论
    )
    
    def __repr__(self):
        return f"<Comment(id={self.id}, user_id={self.user_id}, content_id={self.content_id})>"


# 创建索引
Index('idx_comment_content', Comment.content_id)
Index('idx_comment_user', Comment.user_id)
Index('idx_comment_created', Comment.created_at.desc())
