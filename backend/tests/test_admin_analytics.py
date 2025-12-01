"""
管理后台数据分析功能测试
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from app.models import User, Content, Interaction, Comment, PlaybackProgress
from app.models.content import ContentStatus
from app.models.interaction import InteractionType
from app.services.admin_analytics_service import AdminAnalyticsService


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """创建测试用户"""
    user = User(
        id=str(uuid.uuid4()),
        employee_id="TEST001",
        name="测试用户",
        department="技术部",
        position="工程师"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_get_content_analytics_summary(test_user: User, db_session: AsyncSession):
    """
    测试获取内容分析汇总
    
    需求：45.1
    """
    # 创建测试内容
    content = Content(
        id=str(uuid.uuid4()),
        title="测试视频",
        description="测试描述",
        video_url="https://example.com/video.mp4",
        creator_id=test_user.id,
        status=ContentStatus.PUBLISHED,
        view_count=100,
        like_count=10,
        favorite_count=5,
        comment_count=3,
        share_count=2,
        published_at=datetime.utcnow()
    )
    db_session.add(content)
    await db_session.commit()
    
    # 调用服务
    service = AdminAnalyticsService(db_session)
    summary = await service.get_content_analytics_summary()
    
    # 验证汇总数据
    assert summary.total_contents >= 1
    assert summary.total_views >= 100
    assert summary.total_likes >= 10
    assert summary.total_favorites >= 5
    assert summary.total_comments >= 3
    assert summary.total_shares >= 2


@pytest.mark.asyncio
async def test_get_content_detailed_analytics(test_user: User, db_session: AsyncSession):
    """
    测试获取内容详细分析
    
    需求：45.2
    """
    # 创建测试内容
    content = Content(
        id=str(uuid.uuid4()),
        title="测试视频",
        description="测试描述",
        video_url="https://example.com/video.mp4",
        creator_id=test_user.id,
        status=ContentStatus.PUBLISHED,
        duration=120,
        view_count=50,
        like_count=5,
        favorite_count=3,
        comment_count=2,
        share_count=1,
        published_at=datetime.utcnow()
    )
    db_session.add(content)
    await db_session.commit()
    
    # 创建播放进度记录
    progress = PlaybackProgress(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        content_id=content.id,
        progress_seconds=110.0,
        duration_seconds=120.0,
        progress_percentage=91.67,
        is_completed=1
    )
    db_session.add(progress)
    await db_session.commit()
    
    # 调用服务
    service = AdminAnalyticsService(db_session)
    analytics = await service.get_content_detailed_analytics(content.id)
    
    # 验证响应数据
    assert analytics is not None
    assert analytics.content_id == content.id
    assert analytics.title == content.title
    assert analytics.duration == 120
    assert analytics.view_count == 50
    assert analytics.completion_count == 1  # 一个完播记录
    assert analytics.unique_viewers == 1
    assert analytics.like_count == 5
    assert analytics.favorite_count == 3


@pytest.mark.asyncio
async def test_get_favorite_records(test_user: User, db_session: AsyncSession):
    """
    测试获取收藏记录
    
    需求：49.1
    """
    # 创建测试内容
    content = Content(
        id=str(uuid.uuid4()),
        title="测试视频",
        description="测试描述",
        video_url="https://example.com/video.mp4",
        creator_id=test_user.id,
        status=ContentStatus.PUBLISHED
    )
    db_session.add(content)
    await db_session.commit()
    
    # 创建收藏记录
    interaction = Interaction(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        content_id=content.id,
        type=InteractionType.FAVORITE
    )
    db_session.add(interaction)
    await db_session.commit()
    
    # 调用服务
    service = AdminAnalyticsService(db_session)
    records, total = await service.get_interaction_records("favorite", page=1, page_size=20)
    
    # 验证至少有一条记录
    assert total >= 1
    assert len(records) >= 1
    assert records[0].interaction_type == "favorite"


@pytest.mark.asyncio
async def test_delete_comment(test_user: User, db_session: AsyncSession):
    """
    测试删除评论
    
    需求：49.5
    """
    # 创建测试内容
    content = Content(
        id=str(uuid.uuid4()),
        title="测试视频",
        description="测试描述",
        video_url="https://example.com/video.mp4",
        creator_id=test_user.id,
        status=ContentStatus.PUBLISHED,
        comment_count=1
    )
    db_session.add(content)
    await db_session.commit()
    
    # 创建评论
    comment = Comment(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        content_id=content.id,
        text="这是一条不当评论"
    )
    db_session.add(comment)
    await db_session.commit()
    
    # 调用服务删除评论
    service = AdminAnalyticsService(db_session)
    success = await service.delete_comment(comment.id)
    
    assert success is True
    
    # 验证评论已删除
    await db_session.refresh(content)
    assert content.comment_count == 0


@pytest.mark.asyncio
async def test_export_analytics_report(test_user: User, db_session: AsyncSession):
    """
    测试导出分析报告
    
    需求：45.4
    """
    # 创建测试内容
    content = Content(
        id=str(uuid.uuid4()),
        title="测试视频",
        description="测试描述",
        video_url="https://example.com/video.mp4",
        creator_id=test_user.id,
        status=ContentStatus.PUBLISHED,
        view_count=100,
        like_count=10,
        published_at=datetime.utcnow()
    )
    db_session.add(content)
    await db_session.commit()
    
    # 调用服务导出报告
    service = AdminAnalyticsService(db_session)
    report_data = await service.export_analytics_report(format="csv")
    
    # 验证CSV内容
    content_text = report_data.decode('utf-8-sig')
    assert "内容ID" in content_text  # CSV表头
    assert "标题" in content_text
    assert content.title in content_text
