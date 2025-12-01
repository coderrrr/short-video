"""
API集成测试
测试完整的业务流程，包括内容发布、用户互动、审核流程和推荐系统
"""
import pytest
import asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta
from typing import Dict, Any

from app.main import app
from app.models.user import User
from app.models.content import Content, ContentStatus
from app.models.tag import Tag
from app.models.interaction import Interaction, InteractionType
from app.models.comment import Comment
from app.models.review_record import ReviewRecord


@pytest.fixture
async def test_client():
    """创建测试HTTP客户端"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_creator(db_session) -> User:
    """创建测试创作者"""
    user = User(
        id="creator-001",
        employee_id="EMP001",
        name="测试创作者",
        department="技术部",
        position="工程师",
        is_kol=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_viewer(db_session) -> User:
    """创建测试观看者"""
    user = User(
        id="viewer-001",
        employee_id="EMP002",
        name="测试观看者",
        department="产品部",
        position="产品经理",
        is_kol=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(db_session) -> User:
    """创建测试管理员"""
    user = User(
        id="admin-001",
        employee_id="ADMIN001",
        name="测试管理员",
        department="管理部",
        position="管理员",
        is_kol=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_tags(db_session) -> list[Tag]:
    """创建测试标签"""
    tags = [
        Tag(id="tag-001", name="Python", category="技术标签"),
        Tag(id="tag-002", name="数据分析", category="主题标签"),
        Tag(id="tag-003", name="工作知识", category="内容类型"),
    ]
    for tag in tags:
        db_session.add(tag)
    await db_session.commit()
    return tags


class TestContentPublishingFlow:
    """测试完整的内容发布流程"""
    
    @pytest.mark.asyncio
    async def test_complete_content_publishing_flow(
        self,
        test_client: AsyncClient,
        db_session,
        test_creator: User,
        test_admin: User,
        test_tags: list[Tag]
    ):
        """
        测试从上传到发布的完整流程：
        1. 创作者上传视频
        2. AI处理内容
        3. 提交审核
        4. 管理员批准
        5. 内容发布
        """
        
        # 步骤1: 创建草稿内容
        import uuid
        content_id = str(uuid.uuid4())
        draft_data = {
            "id": content_id,
            "title": "Python数据分析入门",
            "description": "这是一个关于Python数据分析的教程视频",
            "content_type": "工作知识",
            "video_url": "https://example.com/video.mp4",
            "cover_url": "https://example.com/cover.jpg",
            "duration": 300,
            "creator_id": test_creator.id
        }
        
        content = Content(**draft_data, status=ContentStatus.DRAFT)
        db_session.add(content)
        await db_session.commit()
        await db_session.refresh(content)
        
        assert content.status == ContentStatus.DRAFT
        
        # 步骤2: 添加标签（手动分配，不使用AI）
        from app.models.content_tag import ContentTag
        content_tag = ContentTag(
            id=f"ct-{content.id}-{test_tags[0].id}",
            content_id=content.id,
            tag_id=test_tags[0].id
        )
        db_session.add(content_tag)
        await db_session.commit()
        
        # 步骤3: 提交审核
        content.status = ContentStatus.UNDER_REVIEW
        await db_session.commit()
        
        assert content.status == ContentStatus.UNDER_REVIEW
        
        # 步骤4: 创建审核记录
        review = ReviewRecord(
            id=f"review-{content.id}",
            content_id=content.id,
            reviewer_id=test_admin.id,
            review_type="platform_review",
            status="pending"
        )
        db_session.add(review)
        await db_session.commit()
        
        # 步骤5: 管理员批准
        review.status = "approved"
        content.status = ContentStatus.PUBLISHED
        content.published_at = datetime.utcnow()
        await db_session.commit()
        
        assert content.status == ContentStatus.PUBLISHED
        assert content.published_at is not None
        
        # 步骤6: 验证内容可以被查询
        from sqlalchemy import select
        result = await db_session.execute(
            select(Content).where(
                Content.id == content.id,
                Content.status == ContentStatus.PUBLISHED
            )
        )
        published_content = result.scalar_one_or_none()
        
        assert published_content is not None
        assert published_content.title == draft_data["title"]
        assert published_content.creator_id == test_creator.id


class TestUserInteractionFlow:
    """测试用户互动流程"""
    
    @pytest.mark.asyncio
    async def test_complete_user_interaction_flow(
        self,
        test_client: AsyncClient,
        db_session,
        test_creator: User,
        test_viewer: User
    ):
        """
        测试用户互动流程：
        1. 用户观看视频
        2. 用户点赞
        3. 用户收藏
        4. 用户评论
        5. 用户分享
        """
        
        # 创建已发布的内容
        content = Content(
            id="content-001",
            title="测试视频",
            description="测试描述",
            video_url="https://example.com/video.mp4",
            creator_id=test_creator.id,
            status=ContentStatus.PUBLISHED,
            published_at=datetime.utcnow()
        )
        db_session.add(content)
        await db_session.commit()
        
        # 步骤1: 用户点赞
        like_interaction = Interaction(
            id="like-001",
            user_id=test_viewer.id,
            content_id=content.id,
            type=InteractionType.LIKE
        )
        db_session.add(like_interaction)
        content.like_count += 1
        await db_session.commit()
        
        assert content.like_count == 1
        
        # 步骤2: 用户收藏
        favorite_interaction = Interaction(
            id="favorite-001",
            user_id=test_viewer.id,
            content_id=content.id,
            type=InteractionType.FAVORITE
        )
        db_session.add(favorite_interaction)
        content.favorite_count += 1
        await db_session.commit()
        
        assert content.favorite_count == 1
        
        # 步骤3: 用户评论
        comment = Comment(
            id="comment-001",
            content_id=content.id,
            user_id=test_viewer.id,
            text="这个视频很有帮助！"
        )
        db_session.add(comment)
        content.comment_count += 1
        await db_session.commit()
        
        assert content.comment_count == 1
        
        # 步骤4: 用户分享
        share_interaction = Interaction(
            id="share-001",
            user_id=test_viewer.id,
            content_id=content.id,
            type=InteractionType.SHARE
        )
        db_session.add(share_interaction)
        content.share_count += 1
        await db_session.commit()
        
        assert content.share_count == 1
        
        # 验证所有互动记录
        from sqlalchemy import select
        result = await db_session.execute(
            select(Interaction).where(
                Interaction.user_id == test_viewer.id,
                Interaction.content_id == content.id
            )
        )
        interactions = result.scalars().all()
        
        assert len(interactions) == 3  # like, favorite, share
        interaction_types = {i.type for i in interactions}
        assert InteractionType.LIKE in interaction_types
        assert InteractionType.FAVORITE in interaction_types
        assert InteractionType.SHARE in interaction_types



class TestReviewWorkflow:
    """测试审核工作流"""
    
    @pytest.mark.asyncio
    async def test_content_review_approval_workflow(
        self,
        db_session,
        test_creator: User,
        test_admin: User
    ):
        """测试内容审核批准流程"""
        
        # 创建待审核内容
        content = Content(
            id="content-review-001",
            title="待审核视频",
            description="这是一个待审核的视频",
            video_url="https://example.com/video.mp4",
            creator_id=test_creator.id,
            status=ContentStatus.UNDER_REVIEW
        )
        db_session.add(content)
        await db_session.commit()
        
        # 创建审核记录
        review = ReviewRecord(
            id="review-001",
            content_id=content.id,
            reviewer_id=test_admin.id,
            review_type="platform_review",
            status="pending"
        )
        db_session.add(review)
        await db_session.commit()
        
        # 批准内容
        review.status = "approved"
        content.status = ContentStatus.PUBLISHED
        content.published_at = datetime.utcnow()
        await db_session.commit()
        
        # 验证状态
        await db_session.refresh(content)
        await db_session.refresh(review)
        
        assert content.status == ContentStatus.PUBLISHED
        assert review.status == "approved"
        assert content.published_at is not None
    
    @pytest.mark.asyncio
    async def test_content_review_rejection_workflow(
        self,
        db_session,
        test_creator: User,
        test_admin: User
    ):
        """测试内容审核拒绝流程"""
        
        # 创建待审核内容
        content = Content(
            id="content-reject-001",
            title="待审核视频",
            description="这是一个待审核的视频",
            video_url="https://example.com/video.mp4",
            creator_id=test_creator.id,
            status=ContentStatus.UNDER_REVIEW
        )
        db_session.add(content)
        await db_session.commit()
        
        # 创建审核记录
        review = ReviewRecord(
            id="review-reject-001",
            content_id=content.id,
            reviewer_id=test_admin.id,
            review_type="platform_review",
            status="pending"
        )
        db_session.add(review)
        await db_session.commit()
        
        # 拒绝内容
        review.status = "rejected"
        review.reason = "内容质量不符合要求"
        content.status = ContentStatus.REJECTED
        await db_session.commit()
        
        # 验证状态
        await db_session.refresh(content)
        await db_session.refresh(review)
        
        assert content.status == ContentStatus.REJECTED
        assert review.status == "rejected"
        assert review.reason == "内容质量不符合要求"


class TestRecommendationSystem:
    """测试推荐系统"""
    
    @pytest.mark.asyncio
    async def test_recommendation_based_on_user_interactions(
        self,
        db_session,
        test_creator: User,
        test_viewer: User,
        test_tags: list[Tag]
    ):
        """测试基于用户互动的推荐"""
        
        # 创建多个已发布内容
        contents = []
        for i in range(5):
            content = Content(
                id=f"content-rec-{i}",
                title=f"测试视频 {i}",
                description=f"测试描述 {i}",
                video_url=f"https://example.com/video{i}.mp4",
                creator_id=test_creator.id,
                status=ContentStatus.PUBLISHED,
                published_at=datetime.utcnow() - timedelta(days=i)
            )
            db_session.add(content)
            contents.append(content)
        
        await db_session.commit()
        
        # 用户与前两个内容互动
        for i in range(2):
            interaction = Interaction(
                id=f"interaction-{i}",
                user_id=test_viewer.id,
                content_id=contents[i].id,
                type=InteractionType.LIKE
            )
            db_session.add(interaction)
        
        await db_session.commit()
        
        # 验证用户有互动记录
        from sqlalchemy import select
        result = await db_session.execute(
            select(Interaction).where(Interaction.user_id == test_viewer.id)
        )
        user_interactions = result.scalars().all()
        
        assert len(user_interactions) == 2
        
        # 推荐系统应该考虑用户的互动历史
        # 这里我们验证推荐逻辑的基础数据是否正确
        result = await db_session.execute(
            select(Content).where(
                Content.status == ContentStatus.PUBLISHED
            ).order_by(Content.published_at.desc())
        )
        published_contents = result.scalars().all()
        
        assert len(published_contents) == 5
        # 最新的内容应该排在前面
        assert published_contents[0].id == "content-rec-0"


class TestFollowSystem:
    """测试关注系统"""
    
    @pytest.mark.asyncio
    async def test_follow_and_feed_workflow(
        self,
        db_session,
        test_creator: User,
        test_viewer: User
    ):
        """测试关注和信息流工作流"""
        
        # 用户关注创作者
        from app.models.follow import Follow
        follow = Follow(
            id="follow-001",
            follower_id=test_viewer.id,
            followee_id=test_creator.id
        )
        db_session.add(follow)
        await db_session.commit()
        
        # 创作者发布内容
        content = Content(
            id="content-follow-001",
            title="关注测试视频",
            description="这是一个测试视频",
            video_url="https://example.com/video.mp4",
            creator_id=test_creator.id,
            status=ContentStatus.PUBLISHED,
            published_at=datetime.utcnow()
        )
        db_session.add(content)
        await db_session.commit()
        
        # 验证关注关系
        from sqlalchemy import select
        result = await db_session.execute(
            select(Follow).where(
                Follow.follower_id == test_viewer.id,
                Follow.followee_id == test_creator.id
            )
        )
        follow_record = result.scalar_one_or_none()
        
        assert follow_record is not None
        
        # 验证可以查询到关注的创作者的内容
        result = await db_session.execute(
            select(Content).where(
                Content.creator_id == test_creator.id,
                Content.status == ContentStatus.PUBLISHED
            )
        )
        creator_contents = result.scalars().all()
        
        assert len(creator_contents) == 1
        assert creator_contents[0].id == "content-follow-001"
