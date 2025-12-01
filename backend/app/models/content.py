"""
内容模型
"""
from sqlalchemy import Column, String, Text, Integer, BigInteger, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from .base import Base


class ContentStatus(str, Enum):
    """内容状态枚举"""
    DRAFT = "draft"  # 草稿
    UNDER_REVIEW = "under_review"  # 审核中
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已驳回
    PUBLISHED = "published"  # 已发布
    REMOVED = "removed"  # 已下架


class Content(Base):
    """内容表"""
    __tablename__ = "contents"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 基本信息
    title = Column(String(200), nullable=False, comment="标题")
    description = Column(Text, comment="描述")
    video_url = Column(String(500), nullable=False, comment="视频URL")
    cover_url = Column(String(500), comment="封面URL")
    duration = Column(Integer, comment="时长（秒）")
    file_size = Column(BigInteger, comment="文件大小（字节）")
    
    # 创作者
    creator_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="创作者ID")
    
    # 状态
    status = Column(SQLEnum(ContentStatus, values_callable=lambda x: [e.value for e in x]), default=ContentStatus.DRAFT, nullable=False, comment="状态")
    
    # 内容类型
    content_type = Column(String(50), comment="内容类型（工作知识、生活分享、企业文化等）")
    
    # 统计数据
    view_count = Column(Integer, default=0, comment="观看次数")
    like_count = Column(Integer, default=0, comment="点赞数")
    favorite_count = Column(Integer, default=0, comment="收藏数")
    comment_count = Column(Integer, default=0, comment="评论数")
    share_count = Column(Integer, default=0, comment="分享数")
    
    # 精选内容相关（管理后台功能）
    is_featured = Column(Integer, default=0, comment="是否精选（0=否，1=是）")
    featured_priority = Column(Integer, default=0, comment="精选优先级（1-100，数字越大优先级越高）")
    featured_position = Column(String(50), comment="精选位置（homepage, category_top等）")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    published_at = Column(DateTime, comment="发布时间")
    
    # 关系
    creator = relationship("User", back_populates="contents")
    tags = relationship("ContentTag", back_populates="content", cascade="all, delete-orphan")
    interactions = relationship("Interaction", back_populates="content", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="content", cascade="all, delete-orphan")
    shares = relationship("Share", back_populates="content", cascade="all, delete-orphan")
    review_records = relationship("ReviewRecord", back_populates="content", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Content(id={self.id}, title={self.title}, status={self.status})>"


# 创建索引
Index('idx_content_creator', Content.creator_id)
Index('idx_content_status', Content.status)
Index('idx_content_published', Content.published_at.desc())
Index('idx_content_type', Content.content_type)
Index('idx_content_featured', Content.is_featured, Content.featured_priority.desc())
