"""
学习分析和游戏化功能测试
"""
import pytest
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.models import (
    User,
    Content,
    ContentStatus,
    LearningAnalytics,
    LeaderboardEntry,
    Achievement,
    UserAchievement,
    AchievementType
)
from app.services.analytics_service import AnalyticsService
from app.services.gamification_service import GamificationService


@pytest.mark.asyncio
async def test_create_learning_analytics(db_session: AsyncSession):
    """测试创建学习分析记录"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        employee_id="TEST001",
        name="测试用户",
        department="技术部",
        position="工程师"
    )
    db_session.add(user)
    await db_session.commit()
    
    # 创建学习分析服务
    service = AnalyticsService(db_session)
    
    # 获取或创建学习分析记录
    analytics = await service.get_or_create_analytics(user.id)
    
    assert analytics is not None
    assert analytics.user_id == user.id
    assert analytics.total_videos_watched == 0
    assert analytics.total_watch_time == 0
    assert analytics.learning_streak_days == 0


@pytest.mark.asyncio
async def test_update_learning_stats(db_session: AsyncSession):
    """测试更新学习统计"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        employee_id="TEST002",
        name="测试用户2",
        department="技术部",
        position="工程师"
    )
    db_session.add(user)
    
    # 创建测试内容
    content = Content(
        id=str(uuid.uuid4()),
        title="测试视频",
        description="测试描述",
        video_url="https://example.com/video.mp4",
        creator_id=user.id,
        status=ContentStatus.PUBLISHED,
        content_type="工作知识"
    )
    db_session.add(content)
    await db_session.commit()
    
    # 更新学习统计
    service = AnalyticsService(db_session)
    analytics = await service.update_learning_stats(
        user_id=user.id,
        content_id=content.id,
        watch_time=300
    )
    
    assert analytics.total_videos_watched == 1
    assert analytics.total_watch_time == 300
    assert analytics.learning_streak_days == 1
    assert analytics.last_learning_date == date.today()


@pytest.mark.asyncio
async def test_learning_streak_calculation(db_session: AsyncSession):
    """测试学习连续天数计算"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        employee_id="TEST003",
        name="测试用户3",
        department="技术部",
        position="工程师"
    )
    db_session.add(user)
    
    # 创建测试内容
    content = Content(
        id=str(uuid.uuid4()),
        title="测试视频",
        description="测试描述",
        video_url="https://example.com/video.mp4",
        creator_id=user.id,
        status=ContentStatus.PUBLISHED,
        content_type="工作知识"
    )
    db_session.add(content)
    await db_session.commit()
    
    service = AnalyticsService(db_session)
    
    # 第一次学习
    analytics = await service.update_learning_stats(user.id, content.id, 300)
    assert analytics.learning_streak_days == 1
    
    # 同一天再次学习，连续天数不变
    analytics = await service.update_learning_stats(user.id, content.id, 300)
    assert analytics.learning_streak_days == 1


@pytest.mark.asyncio
async def test_initialize_achievements(db_session: AsyncSession):
    """测试初始化成就系统"""
    service = GamificationService(db_session)
    
    # 初始化成就
    await service.initialize_achievements()
    
    # 获取所有成就
    achievements = await service.get_all_achievements()
    
    assert len(achievements) > 0
    # 应该有学习里程碑、贡献里程碑和连续学习里程碑
    types = {ach['achievement_type'] for ach in achievements}
    assert 'learning_milestone' in types
    assert 'contribution_milestone' in types
    assert 'streak_milestone' in types


@pytest.mark.asyncio
async def test_check_and_unlock_achievements(db_session: AsyncSession):
    """测试检查并解锁成就"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        employee_id="TEST004",
        name="测试用户4",
        department="技术部",
        position="工程师"
    )
    db_session.add(user)
    
    # 创建学习分析记录（观看了10个视频）
    analytics = LearningAnalytics(
        id=str(uuid.uuid4()),
        user_id=user.id,
        total_videos_watched=10,
        total_watch_time=3000,
        learning_streak_days=1
    )
    db_session.add(analytics)
    await db_session.commit()
    
    # 初始化成就系统
    gamification_service = GamificationService(db_session)
    await gamification_service.initialize_achievements()
    
    # 检查并解锁成就
    await gamification_service.check_and_unlock_achievements(user.id)
    
    # 获取用户成就
    user_achievements = await gamification_service.get_user_achievements(user.id)
    
    # 应该解锁"初学者"成就（观看10个视频）
    assert len(user_achievements) > 0
    achievement_names = {ach['name'] for ach in user_achievements}
    assert '初学者' in achievement_names


@pytest.mark.asyncio
async def test_update_leaderboard(db_session: AsyncSession):
    """测试更新排行榜"""
    # 创建多个测试用户和学习分析记录
    users = []
    for i in range(3):
        user = User(
            id=str(uuid.uuid4()),
            employee_id=f"TEST00{i+5}",
            name=f"测试用户{i+5}",
            department="技术部",
            position="工程师"
        )
        db_session.add(user)
        users.append(user)
        
        # 创建学习分析记录
        analytics = LearningAnalytics(
            id=str(uuid.uuid4()),
            user_id=user.id,
            total_videos_watched=(i + 1) * 10,
            total_watch_time=(i + 1) * 3600,
            learning_streak_days=i + 1
        )
        db_session.add(analytics)
    
    await db_session.commit()
    
    # 更新排行榜
    service = GamificationService(db_session)
    await service.update_leaderboard()
    
    # 获取排行榜
    leaderboard = await service.get_leaderboard(limit=10)
    
    assert len(leaderboard) >= 3
    # 排行榜应该按得分降序排列
    for i in range(len(leaderboard) - 1):
        assert leaderboard[i]['score'] >= leaderboard[i + 1]['score']


@pytest.mark.asyncio
async def test_get_user_rank(db_session: AsyncSession):
    """测试获取用户排名"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        employee_id="TEST008",
        name="测试用户8",
        department="技术部",
        position="工程师"
    )
    db_session.add(user)
    
    # 创建学习分析记录
    analytics = LearningAnalytics(
        id=str(uuid.uuid4()),
        user_id=user.id,
        total_videos_watched=50,
        total_watch_time=18000,
        learning_streak_days=7
    )
    db_session.add(analytics)
    await db_session.commit()
    
    # 更新排行榜
    service = GamificationService(db_session)
    await service.update_leaderboard()
    
    # 获取用户排名
    rank_info = await service.get_user_rank(user.id)
    
    assert rank_info is not None
    assert rank_info['user_id'] == user.id
    assert rank_info['rank'] > 0
    assert rank_info['score'] > 0


@pytest.mark.asyncio
async def test_get_learning_history(db_session: AsyncSession):
    """测试获取学习历史"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        employee_id="TEST009",
        name="测试用户9",
        department="技术部",
        position="工程师"
    )
    db_session.add(user)
    
    # 创建测试内容
    content = Content(
        id=str(uuid.uuid4()),
        title="测试视频",
        description="测试描述",
        video_url="https://example.com/video.mp4",
        creator_id=user.id,
        status=ContentStatus.PUBLISHED,
        content_type="工作知识"
    )
    db_session.add(content)
    await db_session.commit()
    
    # 更新学习统计
    service = AnalyticsService(db_session)
    await service.update_learning_stats(user.id, content.id, 300)
    
    # 获取学习历史
    history = await service.get_learning_history(user.id, days=7)
    
    assert len(history) > 0
    assert history[0]['date'] == date.today().isoformat()
    assert history[0]['videos_watched'] == 1
    assert history[0]['watch_time'] == 300
