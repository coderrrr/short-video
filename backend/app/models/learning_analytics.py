"""
学习分析数据模型
"""
from sqlalchemy import Column, String, Integer, DateTime, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class LearningAnalytics(Base):
    """学习分析统计表"""
    __tablename__ = "learning_analytics"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # 统计数据
    total_videos_watched = Column(Integer, default=0)  # 总观看视频数
    total_watch_time = Column(Integer, default=0)  # 总观看时间（秒）
    learning_streak_days = Column(Integer, default=0)  # 学习连续天数
    last_learning_date = Column(Date)  # 最后学习日期
    
    # 分类统计（JSON格式存储）
    # 格式: {"工作知识": 10, "生活分享": 5, "企业文化": 3}
    category_stats = Column(String(1000))  # 按分类统计
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="learning_analytics")
    
    __table_args__ = (
        Index('idx_learning_analytics_user', 'user_id'),
    )


class DailyLearningRecord(Base):
    """每日学习记录表"""
    __tablename__ = "daily_learning_records"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    learning_date = Column(Date, nullable=False)
    
    # 当日统计
    videos_watched = Column(Integer, default=0)  # 当日观看视频数
    watch_time = Column(Integer, default=0)  # 当日观看时间（秒）
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_daily_learning_user_date', 'user_id', 'learning_date'),
    )
