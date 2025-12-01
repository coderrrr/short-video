"""
游戏化服务 - 排行榜和成就系统
"""
from datetime import datetime, date
from typing import List, Dict, Optional
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.models import (
    LeaderboardEntry,
    Achievement,
    UserAchievement,
    AchievementType,
    LearningAnalytics,
    Content,
    User
)


class GamificationService:
    """游戏化服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def update_leaderboard(self, period_date: Optional[date] = None):
        """
        更新排行榜
        
        Args:
            period_date: 统计日期，默认为今天
        """
        if period_date is None:
            period_date = date.today()
        
        # 查询所有用户的学习分析数据
        result = await self.db.execute(
            select(LearningAnalytics, User)
            .join(User, LearningAnalytics.user_id == User.id)
        )
        analytics_list = result.all()
        
        # 查询所有用户的创作数量
        content_counts_result = await self.db.execute(
            select(
                Content.creator_id,
                func.count(Content.id).label('count')
            )
            .where(Content.status == 'published')
            .group_by(Content.creator_id)
        )
        content_counts = {row.creator_id: row.count for row in content_counts_result}
        
        # 计算每个用户的得分并排序
        user_scores = []
        for analytics, user in analytics_list:
            # 综合得分计算：观看视频数 * 10 + 观看时间/60 + 创作视频数 * 50
            videos_created = content_counts.get(user.id, 0)
            score = (
                analytics.total_videos_watched * 10 +
                analytics.total_watch_time // 60 +
                videos_created * 50
            )
            
            user_scores.append({
                'user_id': user.id,
                'score': score,
                'videos_watched': analytics.total_videos_watched,
                'watch_time': analytics.total_watch_time,
                'videos_created': videos_created
            })
        
        # 按得分排序
        user_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # 删除当天的旧排行榜记录
        await self.db.execute(
            select(LeaderboardEntry).where(LeaderboardEntry.period_date == period_date)
        )
        existing_entries = (await self.db.execute(
            select(LeaderboardEntry).where(LeaderboardEntry.period_date == period_date)
        )).scalars().all()
        
        for entry in existing_entries:
            await self.db.delete(entry)
        
        # 创建新的排行榜记录
        for rank, user_data in enumerate(user_scores, start=1):
            entry = LeaderboardEntry(
                id=str(uuid.uuid4()),
                user_id=user_data['user_id'],
                rank=rank,
                score=user_data['score'],
                videos_watched=user_data['videos_watched'],
                watch_time=user_data['watch_time'],
                videos_created=user_data['videos_created'],
                period_date=period_date
            )
            self.db.add(entry)
        
        await self.db.commit()
    
    async def get_leaderboard(
        self,
        period_date: Optional[date] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        获取排行榜
        
        Args:
            period_date: 统计日期，默认为今天
            limit: 返回的排名数量
        
        Returns:
            排行榜列表
        """
        if period_date is None:
            period_date = date.today()
        
        result = await self.db.execute(
            select(LeaderboardEntry, User)
            .join(User, LeaderboardEntry.user_id == User.id)
            .where(LeaderboardEntry.period_date == period_date)
            .order_by(LeaderboardEntry.rank)
            .limit(limit)
        )
        
        leaderboard = []
        for entry, user in result:
            leaderboard.append({
                'rank': entry.rank,
                'user_id': user.id,
                'user_name': user.name,
                'avatar_url': user.avatar_url,
                'department': user.department,
                'is_kol': user.is_kol,
                'score': entry.score,
                'videos_watched': entry.videos_watched,
                'watch_time': entry.watch_time,
                'videos_created': entry.videos_created
            })
        
        return leaderboard
    
    async def get_user_rank(
        self,
        user_id: str,
        period_date: Optional[date] = None
    ) -> Optional[Dict]:
        """
        获取用户的排名信息
        
        Args:
            user_id: 用户ID
            period_date: 统计日期，默认为今天
        
        Returns:
            用户排名信息，如果用户不在排行榜中则返回None
        """
        if period_date is None:
            period_date = date.today()
        
        result = await self.db.execute(
            select(LeaderboardEntry, User)
            .join(User, LeaderboardEntry.user_id == User.id)
            .where(
                and_(
                    LeaderboardEntry.user_id == user_id,
                    LeaderboardEntry.period_date == period_date
                )
            )
        )
        
        row = result.first()
        if not row:
            return None
        
        entry, user = row
        return {
            'rank': entry.rank,
            'user_id': user.id,
            'user_name': user.name,
            'avatar_url': user.avatar_url,
            'score': entry.score,
            'videos_watched': entry.videos_watched,
            'watch_time': entry.watch_time,
            'videos_created': entry.videos_created
        }
    
    async def initialize_achievements(self):
        """初始化成就系统（创建预定义的成就）"""
        # 检查是否已经初始化
        result = await self.db.execute(select(func.count(Achievement.id)))
        count = result.scalar()
        
        if count > 0:
            # 已经初始化过了
            return
        
        # 定义预设成就
        achievements = [
            # 学习里程碑
            {
                'name': '初学者',
                'description': '观看10个视频',
                'type': AchievementType.LEARNING_MILESTONE,
                'requirement_value': 10
            },
            {
                'name': '学习达人',
                'description': '观看50个视频',
                'type': AchievementType.LEARNING_MILESTONE,
                'requirement_value': 50
            },
            {
                'name': '学习大师',
                'description': '观看100个视频',
                'type': AchievementType.LEARNING_MILESTONE,
                'requirement_value': 100
            },
            {
                'name': '学习专家',
                'description': '观看500个视频',
                'type': AchievementType.LEARNING_MILESTONE,
                'requirement_value': 500
            },
            # 贡献里程碑
            {
                'name': '初次分享',
                'description': '发布1个视频',
                'type': AchievementType.CONTRIBUTION_MILESTONE,
                'requirement_value': 1
            },
            {
                'name': '活跃创作者',
                'description': '发布10个视频',
                'type': AchievementType.CONTRIBUTION_MILESTONE,
                'requirement_value': 10
            },
            {
                'name': '内容大师',
                'description': '发布50个视频',
                'type': AchievementType.CONTRIBUTION_MILESTONE,
                'requirement_value': 50
            },
            # 连续学习里程碑
            {
                'name': '坚持一周',
                'description': '连续学习7天',
                'type': AchievementType.STREAK_MILESTONE,
                'requirement_value': 7
            },
            {
                'name': '坚持一月',
                'description': '连续学习30天',
                'type': AchievementType.STREAK_MILESTONE,
                'requirement_value': 30
            },
            {
                'name': '坚持百日',
                'description': '连续学习100天',
                'type': AchievementType.STREAK_MILESTONE,
                'requirement_value': 100
            },
        ]
        
        for ach_data in achievements:
            achievement = Achievement(
                id=str(uuid.uuid4()),
                name=ach_data['name'],
                description=ach_data['description'],
                achievement_type=ach_data['type'],
                requirement_value=ach_data['requirement_value'],
                requirement_description=ach_data['description']
            )
            self.db.add(achievement)
        
        await self.db.commit()
    
    async def check_and_unlock_achievements(self, user_id: str):
        """
        检查并解锁用户的成就
        
        Args:
            user_id: 用户ID
        """
        # 获取用户的学习分析数据
        analytics_result = await self.db.execute(
            select(LearningAnalytics).where(LearningAnalytics.user_id == user_id)
        )
        analytics = analytics_result.scalar_one_or_none()
        
        if not analytics:
            return
        
        # 获取用户创作的视频数量
        content_count_result = await self.db.execute(
            select(func.count(Content.id))
            .where(
                and_(
                    Content.creator_id == user_id,
                    Content.status == 'published'
                )
            )
        )
        videos_created = content_count_result.scalar()
        
        # 获取所有成就
        achievements_result = await self.db.execute(select(Achievement))
        all_achievements = achievements_result.scalars().all()
        
        # 获取用户已解锁的成就
        unlocked_result = await self.db.execute(
            select(UserAchievement.achievement_id)
            .where(UserAchievement.user_id == user_id)
        )
        unlocked_ids = {row[0] for row in unlocked_result}
        
        # 检查每个成就
        for achievement in all_achievements:
            if achievement.id in unlocked_ids:
                continue  # 已经解锁
            
            should_unlock = False
            
            if achievement.achievement_type == AchievementType.LEARNING_MILESTONE:
                should_unlock = analytics.total_videos_watched >= achievement.requirement_value
            elif achievement.achievement_type == AchievementType.CONTRIBUTION_MILESTONE:
                should_unlock = videos_created >= achievement.requirement_value
            elif achievement.achievement_type == AchievementType.STREAK_MILESTONE:
                should_unlock = analytics.learning_streak_days >= achievement.requirement_value
            
            if should_unlock:
                # 解锁成就
                user_achievement = UserAchievement(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    achievement_id=achievement.id
                )
                self.db.add(user_achievement)
        
        await self.db.commit()
    
    async def get_user_achievements(self, user_id: str) -> List[Dict]:
        """
        获取用户的成就列表
        
        Args:
            user_id: 用户ID
        
        Returns:
            成就列表
        """
        result = await self.db.execute(
            select(Achievement, UserAchievement)
            .join(UserAchievement, Achievement.id == UserAchievement.achievement_id)
            .where(UserAchievement.user_id == user_id)
            .order_by(UserAchievement.unlocked_at.desc())
        )
        
        achievements = []
        for achievement, user_achievement in result:
            achievements.append({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon_url': achievement.icon_url,
                'achievement_type': achievement.achievement_type.value,
                'unlocked_at': user_achievement.unlocked_at.isoformat()
            })
        
        return achievements
    
    async def get_all_achievements(self) -> List[Dict]:
        """
        获取所有成就定义
        
        Returns:
            所有成就列表
        """
        result = await self.db.execute(
            select(Achievement).order_by(Achievement.achievement_type, Achievement.requirement_value)
        )
        achievements = result.scalars().all()
        
        return [
            {
                'id': ach.id,
                'name': ach.name,
                'description': ach.description,
                'icon_url': ach.icon_url,
                'achievement_type': ach.achievement_type.value,
                'requirement_value': ach.requirement_value,
                'requirement_description': ach.requirement_description
            }
            for ach in achievements
        ]
