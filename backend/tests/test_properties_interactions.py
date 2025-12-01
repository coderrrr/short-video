"""
基于属性的测试 - 互动操作

本文件实现设计文档中定义的属性21-26的基于属性的测试。
使用Hypothesis框架进行属性测试，每个测试至少运行100次迭代。
"""
import pytest
import uuid
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
from datetime import datetime

from app.services.user_service import UserService
from app.services.content_service import ContentService
from app.models.user import User
from app.models.content import Content, ContentStatus
from app.models.interaction import Interaction, InteractionType
from app.models.follow import Follow
from fastapi import HTTPException


# ==================== 测试数据生成策略 ====================

@st.composite
def user_ids_strategy(draw, min_size=0, max_size=20):
    """生成用户ID列表"""
    count = draw(st.integers(min_value=min_size, max_value=max_size))
    return [str(uuid.uuid4()) for _ in range(count)]


# ==================== 属性测试 ====================

# Feature: enterprise-video-learning-platform, Property 21: 收藏操作幂等性
@given(
    repeat_count=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_property_21_favorite_idempotence(repeat_count, db_session):
    """
    属性21：收藏操作幂等性
    
    对于任何用户和内容，多次执行收藏操作应产生与单次操作相同的结果
    （收藏列表包含该内容）
    
    验证需求：15.1
    """
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        employee_id=f"TEST{user_id[:8]}",
        name="测试用户",
        department="测试部门",
        position="测试岗位"
    )
    db_session.add(user)
    
    # 创建测试内容
    content_id = str(uuid.uuid4())
    content = Content(
        id=content_id,
        title="测试视频",
        description="测试描述",
        video_url="https://example.com/video.mp4",
        file_size=1024,
        creator_id=user_id,
        status=ContentStatus.PUBLISHED,
        content_type="工作知识",
        created_at=datetime.utcnow()
    )
    db_session.add(content)
    await db_session.commit()
    
    # 创建UserService实例
    service = UserService(db_session)
    
    # 多次执行收藏操作
    for i in range(repeat_count):
        try:
            await service.favorite_content(user_id, content_id)
        except HTTPException:
            # 如果已收藏，应该幂等地返回或不抛出错误
            pass
    
    # 验证收藏列表
    favorite_list = await service.get_favorite_list(user_id)
    
    # 幂等性：无论执行多少次，收藏列表应该只包含该内容一次
    assert len(favorite_list) == 1
    assert favorite_list[0].id == content_id
    
    # 验证数据库中的收藏记录数
    from sqlalchemy import select, func, and_
    count_result = await db_session.execute(
        select(func.count(Interaction.id)).where(
            and_(
                Interaction.user_id == user_id,
                Interaction.content_id == content_id,
                Interaction.type == InteractionType.FAVORITE
            )
        )
    )
    favorite_count = count_result.scalar()
    
    # 应该只有一条收藏记录
    assert favorite_count == 1


# Feature: enterprise-video-learning-platform, Property 22: 取消收藏正确性
@given(
    should_favorite_first=st.booleans()
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_property_22_unfavorite_correctness(should_favorite_first, db_session):
    """
    属性22：取消收藏正确性
    
    对于任何已收藏的内容，执行取消收藏操作后，
    该内容不应出现在用户的收藏列表中
    
    验证需求：15.3
    """
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        employee_id=f"TEST{user_id[:8]}",
        name="测试用户",
        department="测试部门",
        position="测试岗位"
    )
    db_session.add(user)
    
    # 创建测试内容
    content_id = str(uuid.uuid4())
    content = Content(
        id=content_id,
        title="测试视频",
        description="测试描述",
        video_url="https://example.com/video.mp4",
        file_size=1024,
        creator_id=user_id,
        status=ContentStatus.PUBLISHED,
        content_type="工作知识",
        created_at=datetime.utcnow()
    )
    db_session.add(content)
    await db_session.commit()
    
    # 创建UserService实例
    service = UserService(db_session)
    
    if should_favorite_first:
        # 先收藏
        await service.favorite_content(user_id, content_id)
        
        # 验证已收藏
        favorite_list_before = await service.get_favorite_list(user_id)
        assert len(favorite_list_before) == 1
        assert favorite_list_before[0].id == content_id
        
        # 取消收藏
        result = await service.unfavorite_content(user_id, content_id)
        assert result is True
        
        # 验证收藏列表中不再包含该内容
        favorite_list_after = await service.get_favorite_list(user_id)
        assert len(favorite_list_after) == 0
        assert content_id not in [c.id for c in favorite_list_after]
    else:
        # 如果没有先收藏，取消收藏应该失败
        with pytest.raises(HTTPException) as exc_info:
            await service.unfavorite_content(user_id, content_id)
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "未收藏该内容"


# Feature: enterprise-video-learning-platform, Property 23: 点赞计数一致性
@given(
    user_count=st.integers(min_value=0, max_value=50)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_property_23_like_count_consistency(user_count, db_session):
    """
    属性23：点赞计数一致性
    
    对于任何内容，其点赞计数应等于点赞该内容的唯一用户数量
    
    验证需求：17.1, 17.2, 17.4
    """
    # 创建内容创作者
    creator_id = str(uuid.uuid4())
    creator = User(
        id=creator_id,
        employee_id=f"CREATOR{creator_id[:8]}",
        name="创作者",
        department="测试部门",
        position="测试岗位"
    )
    db_session.add(creator)
    
    # 创建测试内容
    content_id = str(uuid.uuid4())
    content = Content(
        id=content_id,
        title="测试视频",
        description="测试描述",
        video_url="https://example.com/video.mp4",
        file_size=1024,
        creator_id=creator_id,
        status=ContentStatus.PUBLISHED,
        content_type="工作知识",
        like_count=0,
        created_at=datetime.utcnow()
    )
    db_session.add(content)
    await db_session.commit()
    
    # 创建多个用户并点赞
    user_ids = []
    for i in range(user_count):
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            employee_id=f"TEST{user_id[:8]}",
            name=f"测试用户{i}",
            department="测试部门",
            position="测试岗位"
        )
        db_session.add(user)
        user_ids.append(user_id)
    
    await db_session.commit()
    
    # 创建UserService实例
    service = UserService(db_session)
    
    # 每个用户点赞内容
    for user_id in user_ids:
        await service.like_content(user_id, content_id)
    
    # 刷新内容对象
    await db_session.refresh(content)
    
    # 验证点赞计数
    assert content.like_count == user_count
    
    # 验证数据库中的点赞记录数
    from sqlalchemy import select, func, and_
    count_result = await db_session.execute(
        select(func.count(Interaction.id)).where(
            and_(
                Interaction.content_id == content_id,
                Interaction.type == InteractionType.LIKE
            )
        )
    )
    like_records = count_result.scalar()
    
    # 点赞记录数应该等于用户数
    assert like_records == user_count
    
    # 内容的点赞计数应该等于点赞记录数
    assert content.like_count == like_records


# Feature: enterprise-video-learning-platform, Property 24: 关注关系对称性
@given(
    should_follow=st.booleans()
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_property_24_follow_relationship_symmetry(should_follow, db_session):
    """
    属性24：关注关系对称性
    
    对于任何用户A和用户B，如果A关注B，则B的关注者列表应包含A，
    且A的关注列表应包含B
    
    验证需求：11.1, 11.5
    """
    # 创建用户A
    user_a_id = str(uuid.uuid4())
    user_a = User(
        id=user_a_id,
        employee_id=f"USERA{user_a_id[:8]}",
        name="用户A",
        department="测试部门",
        position="测试岗位"
    )
    db_session.add(user_a)
    
    # 创建用户B
    user_b_id = str(uuid.uuid4())
    user_b = User(
        id=user_b_id,
        employee_id=f"USERB{user_b_id[:8]}",
        name="用户B",
        department="测试部门",
        position="测试岗位"
    )
    db_session.add(user_b)
    await db_session.commit()
    
    # 创建UserService实例
    service = UserService(db_session)
    
    if should_follow:
        # A关注B
        follow = await service.follow_user(user_a_id, user_b_id)
        assert follow is not None
        
        # 验证A的关注列表包含B
        following_list = await service.get_following_list(user_a_id)
        assert len(following_list) == 1
        assert following_list[0].id == user_b_id
        
        # 验证B的粉丝列表包含A
        followers_list = await service.get_followers_list(user_b_id)
        assert len(followers_list) == 1
        assert followers_list[0].id == user_a_id
        
        # 验证关注状态
        is_following = await service.is_following(user_a_id, user_b_id)
        assert is_following is True
        
        # 验证关注计数
        follow_counts_a = await service.get_follow_counts(user_a_id)
        assert follow_counts_a["following_count"] == 1
        assert follow_counts_a["followers_count"] == 0
        
        follow_counts_b = await service.get_follow_counts(user_b_id)
        assert follow_counts_b["following_count"] == 0
        assert follow_counts_b["followers_count"] == 1
    else:
        # 如果不关注，列表应该为空
        following_list = await service.get_following_list(user_a_id)
        assert len(following_list) == 0
        
        followers_list = await service.get_followers_list(user_b_id)
        assert len(followers_list) == 0
        
        is_following = await service.is_following(user_a_id, user_b_id)
        assert is_following is False


# Feature: enterprise-video-learning-platform, Property 25: 取消关注清理
@given(
    should_follow_first=st.booleans()
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_property_25_unfollow_cleanup(should_follow_first, db_session):
    """
    属性25：取消关注清理
    
    对于任何用户取消关注创作者的操作，该创作者的内容不应再出现在
    用户的关注信息流中
    
    验证需求：11.4
    """
    # 创建关注者
    follower_id = str(uuid.uuid4())
    follower = User(
        id=follower_id,
        employee_id=f"FOLLOWER{follower_id[:8]}",
        name="关注者",
        department="测试部门",
        position="测试岗位"
    )
    db_session.add(follower)
    
    # 创建创作者
    creator_id = str(uuid.uuid4())
    creator = User(
        id=creator_id,
        employee_id=f"CREATOR{creator_id[:8]}",
        name="创作者",
        department="测试部门",
        position="测试岗位"
    )
    db_session.add(creator)
    
    # 创建创作者的内容
    content_id = str(uuid.uuid4())
    content = Content(
        id=content_id,
        title="创作者的视频",
        description="测试描述",
        video_url="https://example.com/video.mp4",
        file_size=1024,
        creator_id=creator_id,
        status=ContentStatus.PUBLISHED,
        content_type="工作知识",
        published_at=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    db_session.add(content)
    await db_session.commit()
    
    # 创建UserService实例
    service = UserService(db_session)
    
    if should_follow_first:
        # 先关注
        await service.follow_user(follower_id, creator_id)
        
        # 验证关注信息流包含创作者的内容
        feed_before = await service.get_following_feed(follower_id)
        assert len(feed_before) == 1
        assert feed_before[0].id == content_id
        
        # 取消关注
        result = await service.unfollow_user(follower_id, creator_id)
        assert result is True
        
        # 验证关注信息流不再包含创作者的内容
        feed_after = await service.get_following_feed(follower_id)
        assert len(feed_after) == 0
        assert content_id not in [c.id for c in feed_after]
    else:
        # 如果没有先关注，信息流应该为空
        feed = await service.get_following_feed(follower_id)
        assert len(feed) == 0
        
        # 取消关注应该失败
        with pytest.raises(HTTPException) as exc_info:
            await service.unfollow_user(follower_id, creator_id)
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "未关注该用户"


# Feature: enterprise-video-learning-platform, Property 26: 级联删除一致性
@given(
    interaction_types=st.lists(
        st.sampled_from([InteractionType.FAVORITE, InteractionType.LIKE, InteractionType.BOOKMARK]),
        min_size=0,
        max_size=3,
        unique=True
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_property_26_cascade_delete_consistency(interaction_types, db_session):
    """
    属性26：级联删除一致性
    
    对于任何被删除的内容，所有相关的收藏、点赞、评论、标记记录
    应被清理或标记为无效
    
    验证需求：15.4
    
    注意：本测试验证当内容被删除时，相关的互动记录也应该被级联删除
    """
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        employee_id=f"TEST{user_id[:8]}",
        name="测试用户",
        department="测试部门",
        position="测试岗位"
    )
    db_session.add(user)
    
    # 创建测试内容（草稿状态，以便可以删除）
    content_id = str(uuid.uuid4())
    content = Content(
        id=content_id,
        title="测试视频",
        description="测试描述",
        video_url="https://example.com/video.mp4",
        file_size=1024,
        creator_id=user_id,
        status=ContentStatus.DRAFT,
        content_type="工作知识",
        created_at=datetime.utcnow()
    )
    db_session.add(content)
    await db_session.commit()
    
    # 创建各种互动记录
    interaction_ids = []
    for interaction_type in interaction_types:
        interaction_id = str(uuid.uuid4())
        interaction = Interaction(
            id=interaction_id,
            user_id=user_id,
            content_id=content_id,
            type=interaction_type,
            created_at=datetime.utcnow()
        )
        db_session.add(interaction)
        interaction_ids.append(interaction_id)
    
    await db_session.commit()
    
    # 验证互动记录存在
    from sqlalchemy import select
    for interaction_id in interaction_ids:
        result = await db_session.execute(
            select(Interaction).where(Interaction.id == interaction_id)
        )
        interaction = result.scalar_one_or_none()
        assert interaction is not None
    
    # 删除内容（通过ContentService）
    content_service = ContentService(db_session)
    result = await content_service.delete_draft(content_id, user_id)
    assert result is True
    
    # 验证内容已被删除
    deleted_content = await content_service.get_content(content_id)
    assert deleted_content is None
    
    # 验证相关的互动记录也被级联删除
    for interaction_id in interaction_ids:
        result = await db_session.execute(
            select(Interaction).where(Interaction.id == interaction_id)
        )
        interaction = result.scalar_one_or_none()
        # 由于设置了cascade="all, delete-orphan"，互动记录应该被删除
        assert interaction is None
