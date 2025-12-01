"""
举报记录模型
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import Base


class ReportReason(str, enum.Enum):
    """举报原因枚举"""
    INAPPROPRIATE_CONTENT = "inappropriate_content"  # 不当内容
    SPAM = "spam"  # 垃圾信息
    HARASSMENT = "harassment"  # 骚扰
    FALSE_INFORMATION = "false_information"  # 虚假信息
    COPYRIGHT_VIOLATION = "copyright_violation"  # 侵权
    VIOLENCE = "violence"  # 暴力内容
    HATE_SPEECH = "hate_speech"  # 仇恨言论
    OTHER = "other"  # 其他


class ReportStatus(str, enum.Enum):
    """举报状态枚举"""
    PENDING = "pending"  # 待处理
    REVIEWING = "reviewing"  # 审核中
    RESOLVED = "resolved"  # 已处理
    REJECTED = "rejected"  # 已驳回


class Report(Base):
    """举报记录表"""
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True)
    content_id = Column(String(36), ForeignKey("contents.id"), nullable=False)
    reporter_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # 举报原因
    reason = Column(SQLEnum(ReportReason), nullable=False)
    description = Column(Text)  # 详细描述
    
    # 举报状态
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.PENDING, nullable=False)
    
    # 处理信息
    handler_id = Column(String(36), ForeignKey("users.id"))  # 处理人
    handler_note = Column(Text)  # 处理备注
    handled_at = Column(DateTime)  # 处理时间
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    content = relationship("Content", foreign_keys=[content_id])
    reporter = relationship("User", foreign_keys=[reporter_id])
    handler = relationship("User", foreign_keys=[handler_id])
    
    def __repr__(self):
        return f"<Report(id={self.id}, content_id={self.content_id}, reason={self.reason}, status={self.status})>"
