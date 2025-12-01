"""
排行榜和游戏化数据模型
"""
from sqlalchemy import Column, String, Integer, DateTime, Date, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from .base import Base


class AchievementType(str, Enum):
    """成就类型"""
    LEARNING_MILESTONE = "learning_milestone"  # 学习里程碑
    CONTRIBUTION_MILESTONE = "contribution_milestone"  # 贡献里程碑
    STREAK_MILESTONE = "streak_milestone"  # 连续学习里程碑
    SOCIAL_MILESTONE = "social_milestone"  # 社交里程碑


class LeaderboardEntry(Base):
    """排行榜条目表"""
    __tablename__ = "leaderboard_entries"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # 排名数据
    rank = Column(Integer)  # 排名
    score = Column(Integer, default=0)  # 综合得分
    
    # 统计指标
    videos_watched = Column(Integer, default=0)  # 观看视频数
    watch_time = Column(Integer, default=0)  # 观看时间（秒）
    videos_created = Column(Integer, default=0)  # 创作视频数
    
    # 排行榜周期
    period_date = Column(Date, nullable=False)  # 统计日期（每日更新）
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="leaderboard_entries")
    
    __table_args__ = (
        Index('idx_leaderboard_date_rank', 'period_date', 'rank'),
        Index('idx_leaderboard_user_date', 'user_id', 'period_date'),
    )


class Achievement(Base):
    """成就定义表"""
    __tablename__ = "achievements"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)  # 成就名称
    description = Column(String(500))  # 成就描述
    icon_url = Column(String(500))  # 成就图标URL
    
    achievement_type = Column(SQLEnum(AchievementType), nullable=False)
    
    # 解锁条件
    requirement_value = Column(Integer, nullable=False)  # 要求的数值（如观看100个视频）
    requirement_description = Column(String(200))  # 条件描述
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user_achievements = relationship("UserAchievement", back_populates="achievement")


class UserAchievement(Base):
    """用户成就表"""
    __tablename__ = "user_achievements"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    achievement_id = Column(String(36), ForeignKey("achievements.id"), nullable=False)
    
    unlocked_at = Column(DateTime, default=datetime.utcnow)  # 解锁时间
    
    # 关系
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")
    
    __table_args__ = (
        Index('idx_user_achievement_user', 'user_id'),
        Index('idx_user_achievement_achievement', 'achievement_id'),
    )
