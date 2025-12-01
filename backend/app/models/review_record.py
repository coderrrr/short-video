"""
审核记录模型
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class ReviewRecord(Base):
    """审核记录表"""
    __tablename__ = "review_records"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 外键
    content_id = Column(String(36), ForeignKey("contents.id"), nullable=False, comment="内容ID")
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="审核员ID")
    
    # 审核信息
    review_type = Column(String(20), comment="审核类型（platform_review, expert_review, ai_review）")
    status = Column(String(20), comment="审核状态（approved, rejected, pending）")
    reason = Column(Text, comment="拒绝原因")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关系
    content = relationship("Content", back_populates="review_records")
    reviewer = relationship("User", back_populates="review_records")
    
    def __repr__(self):
        return f"<ReviewRecord(id={self.id}, content_id={self.content_id}, status={self.status})>"
