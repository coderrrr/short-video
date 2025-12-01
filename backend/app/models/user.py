"""
用户模型
"""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 基本信息
    employee_id = Column(String(50), unique=True, nullable=False, index=True, comment="员工ID")
    name = Column(String(100), nullable=False, comment="姓名")
    avatar_url = Column(String(500), comment="头像URL")
    department = Column(String(100), comment="部门")
    position = Column(String(100), comment="岗位")
    
    # KOL标识
    is_kol = Column(Boolean, default=False, comment="是否为KOL")
    
    # 管理员标识
    is_admin = Column(Boolean, default=False, comment="是否为管理员")
    
    # 认证信息
    password_hash = Column(String(255), comment="密码哈希")
    
    # 软删除
    is_deleted = Column(Boolean, default=False, comment="是否已删除")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    contents = relationship("Content", back_populates="creator", cascade="all, delete-orphan")
    followers = relationship(
        "Follow",
        foreign_keys="Follow.followee_id",
        back_populates="followee",
        cascade="all, delete-orphan"
    )
    following = relationship(
        "Follow",
        foreign_keys="Follow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan"
    )
    interactions = relationship("Interaction", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    shares = relationship("Share", back_populates="user", cascade="all, delete-orphan")
    review_records = relationship("ReviewRecord", back_populates="reviewer", cascade="all, delete-orphan")
    learning_analytics = relationship("LearningAnalytics", back_populates="user", uselist=False, cascade="all, delete-orphan")
    leaderboard_entries = relationship("LeaderboardEntry", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, employee_id={self.employee_id})>"
