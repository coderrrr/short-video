"""
学习分析服务
"""
import json
from datetime import datetime, date, timedelta
from typing import Dict, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.models import (
    LearningAnalytics,
    DailyLearningRecord,
    PlaybackProgress,
    Content,
    User
)


class AnalyticsService:
    """学习分析服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_analytics(self, user_id: str) -> LearningAnalytics:
        """获取或创建用户的学习分析记录"""
        result = await self.db.execute(
            select(LearningAnalytics).where(LearningAnalytics.user_id == user_id)
        )
        analytics = result.scalar_one_or_none()
        
        if not analytics:
            analytics = LearningAnalytics(
                id=str(uuid.uuid4()),
                user_id=user_id,
                total_videos_watched=0,
                total_watch_time=0,
                learning_streak_days=0,
                category_stats=json.dumps({})
            )
            self.db.add(analytics)
            await self.db.commit()
            await self.db.refresh(analytics)
        
        return analytics
    
    async def update_learning_stats(
        self,
        user_id: str,
        content_id: str,
        watch_time: int
    ) -> LearningAnalytics:
        """
        更新学习统计数据
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            watch_time: 观看时间（秒）
        
        Returns:
            更新后的学习分析记录
        """
        # 获取内容信息
        content_result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = content_result.scalar_one_or_none()
        
        if not content:
            raise ValueError(f"Content {content_id} not found")
        
        # 获取或创建学习分析记录
        analytics = await self.get_or_create_analytics(user_id)
        
        # 更新总观看视频数和总观看时间
        analytics.total_videos_watched += 1
        analytics.total_watch_time += watch_time
        
        # 更新分类统计
        category_stats = json.loads(analytics.category_stats) if analytics.category_stats else {}
        content_type = content.content_type or "未分类"
        category_stats[content_type] = category_stats.get(content_type, 0) + 1
        analytics.category_stats = json.dumps(category_stats, ensure_ascii=False)
        
        # 更新学习连续天数
        today = date.today()
        if analytics.last_learning_date:
            days_diff = (today - analytics.last_learning_date).days
            if days_diff == 1:
                # 连续学习
                analytics.learning_streak_days += 1
            elif days_diff > 1:
                # 中断了，重新开始
                analytics.learning_streak_days = 1
            # days_diff == 0 表示今天已经学习过，不更新连续天数
        else:
            # 第一次学习
            analytics.learning_streak_days = 1
        
        analytics.last_learning_date = today
        analytics.updated_at = datetime.utcnow()
        
        # 更新每日学习记录
        await self._update_daily_record(user_id, today, watch_time)
        
        await self.db.commit()
        await self.db.refresh(analytics)
        
        return analytics
    
    async def _update_daily_record(
        self,
        user_id: str,
        learning_date: date,
        watch_time: int
    ):
        """更新每日学习记录"""
        result = await self.db.execute(
            select(DailyLearningRecord).where(
                and_(
                    DailyLearningRecord.user_id == user_id,
                    DailyLearningRecord.learning_date == learning_date
                )
            )
        )
        daily_record = result.scalar_one_or_none()
        
        if daily_record:
            daily_record.videos_watched += 1
            daily_record.watch_time += watch_time
            daily_record.updated_at = datetime.utcnow()
        else:
            daily_record = DailyLearningRecord(
                id=str(uuid.uuid4()),
                user_id=user_id,
                learning_date=learning_date,
                videos_watched=1,
                watch_time=watch_time
            )
            self.db.add(daily_record)
        
        await self.db.commit()
    
    async def get_learning_analytics(self, user_id: str) -> Dict:
        """
        获取用户的学习分析数据
        
        Returns:
            包含学习统计的字典
        """
        analytics = await self.get_or_create_analytics(user_id)
        
        # 解析分类统计
        category_stats = json.loads(analytics.category_stats) if analytics.category_stats else {}
        
        return {
            "total_videos_watched": analytics.total_videos_watched,
            "total_watch_time": analytics.total_watch_time,
            "learning_streak_days": analytics.learning_streak_days,
            "last_learning_date": analytics.last_learning_date.isoformat() if analytics.last_learning_date else None,
            "category_breakdown": category_stats
        }
    
    async def get_learning_history(
        self,
        user_id: str,
        days: int = 30
    ) -> list:
        """
        获取用户的学习历史记录
        
        Args:
            user_id: 用户ID
            days: 查询最近多少天的记录
        
        Returns:
            每日学习记录列表
        """
        start_date = date.today() - timedelta(days=days)
        
        result = await self.db.execute(
            select(DailyLearningRecord)
            .where(
                and_(
                    DailyLearningRecord.user_id == user_id,
                    DailyLearningRecord.learning_date >= start_date
                )
            )
            .order_by(DailyLearningRecord.learning_date.desc())
        )
        records = result.scalars().all()
        
        return [
            {
                "date": record.learning_date.isoformat(),
                "videos_watched": record.videos_watched,
                "watch_time": record.watch_time
            }
            for record in records
        ]
    
    async def calculate_watch_time_by_category(
        self,
        user_id: str
    ) -> Dict[str, int]:
        """
        计算用户按分类的观看时间
        
        Returns:
            分类到观看时间的映射
        """
        # 查询用户的所有播放进度记录
        result = await self.db.execute(
            select(
                Content.content_type,
                func.sum(PlaybackProgress.watch_time).label('total_time')
            )
            .join(Content, PlaybackProgress.content_id == Content.id)
            .where(PlaybackProgress.user_id == user_id)
            .group_by(Content.content_type)
        )
        
        category_times = {}
        for row in result:
            content_type = row.content_type or "未分类"
            total_time = row.total_time or 0
            category_times[content_type] = total_time
        
        return category_times
