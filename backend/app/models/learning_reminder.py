"""
学习提醒模型
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class LearningReminder(Base):
    """学习提醒模型"""
    __tablename__ = "learning_reminders"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # 提醒设置
    enabled = Column(Boolean, default=True, comment="是否启用提醒")
    frequency = Column(String(20), nullable=False, comment="提醒频率：daily, weekly, custom")
    time_of_day = Column(String(5), comment="提醒时间（HH:MM格式）")
    days_of_week = Column(String(50), comment="每周提醒日期（逗号分隔，如：1,3,5表示周一、周三、周五）")
    
    # 下次提醒时间
    next_reminder_at = Column(DateTime, comment="下次提醒时间")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", backref="learning_reminders")
    
    def __repr__(self):
        return f"<LearningReminder user_id={self.user_id} frequency={self.frequency}>"
