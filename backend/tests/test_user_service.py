"""
用户服务测试
"""
import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, UploadFile
from io import BytesIO

from app.models.user import User
from app.services.user_service import UserService
from app.schemas.user_schemas import UserCreate, UserUpdate


@pytest.fixture
async def user_service(db_session: AsyncSession):
    """创建用户服务实例"""
    return UserService(db_session)


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """创建测试用户"""
    user = User(
        id=str(uuid.uuid4()),
        employee_id="TEST001",
        name="测试用户",
        department="技术部",
        position="工程师",
        is_kol=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_user(user_service: UserService):
    """测试创建用户"""
    user_data = UserCreate(
        employee_id="TEST002",
        name="新用户",
        department="产品部",
        position="产品经理"
    )
    
    user = await user_service.create_user(user_data)
    
    assert user.id is not None
    assert user.employee_id == "TEST002"
    assert user.name == "新用户"
    assert user.department == "产品部"
    assert user.position == "产品经理"
    assert user.is_kol is False


@pytest.mark.asyncio
async def test_create_user_duplicate_employee_id(user_service: UserService, test_user: User):
    """测试创建重复员工ID的用户应该失败"""
    user_data = UserCreate(
        employee_id=test_user.employee_id,
        name="重复用户",
        department="技术部",
        position="工程师"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await user_service.create_user(user_data)
    
    assert exc_info.value.status_code == 400
    assert "已存在" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_user_by_id(user_service: UserService, test_user: User):
    """测试根据ID获取用户"""
    user = await user_service.get_user_by_id(test_user.id)
    
    assert user is not None
    assert user.id == test_user.id
    assert user.employee_id == test_user.employee_id


@pytest.mark.asyncio
async def test_get_user_by_employee_id(user_service: UserService, test_user: User):
    """测试根据员工ID获取用户"""
    user = await user_service.get_user_by_employee_id(test_user.employee_id)
    
    assert user is not None
    assert user.id == test_user.id
    assert user.employee_id == test_user.employee_id


@pytest.mark.asyncio
async def test_update_user(user_service: UserService, test_user: User):
    """测试更新用户信息"""
    update_data = UserUpdate(
        name="更新后的名字",
        department="新部门",
        position="新岗位"
    )
    
    updated_user = await user_service.update_user(test_user.id, update_data)
    
    assert updated_user.name == "更新后的名字"
    assert updated_user.department == "新部门"
    assert updated_user.position == "新岗位"


@pytest.mark.asyncio
async def test_update_user_not_found(user_service: UserService):
    """测试更新不存在的用户应该失败"""
    update_data = UserUpdate(name="新名字")
    
    with pytest.raises(HTTPException) as exc_info:
        await user_service.update_user("non-existent-id", update_data)
    
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_kol_status(user_service: UserService, test_user: User):
    """测试更新KOL状态"""
    # 设置为KOL
    updated_user = await user_service.update_kol_status(test_user.id, True)
    assert updated_user.is_kol is True
    
    # 取消KOL
    updated_user = await user_service.update_kol_status(test_user.id, False)
    assert updated_user.is_kol is False


@pytest.mark.asyncio
async def test_authenticate_user(user_service: UserService, test_user: User):
    """测试用户认证"""
    user = await user_service.authenticate_user(test_user.employee_id)
    
    assert user is not None
    assert user.id == test_user.id


@pytest.mark.asyncio
async def test_authenticate_user_not_found(user_service: UserService):
    """测试认证不存在的用户"""
    user = await user_service.authenticate_user("non-existent-employee-id")
    
    assert user is None


@pytest.mark.asyncio
async def test_get_users(user_service: UserService, test_user: User):
    """测试获取用户列表"""
    users = await user_service.get_users(skip=0, limit=10)
    
    assert len(users) > 0
    assert any(u.id == test_user.id for u in users)


@pytest.mark.asyncio
async def test_get_users_filter_kol(user_service: UserService, test_user: User):
    """测试筛选KOL用户"""
    # 设置测试用户为KOL
    await user_service.update_kol_status(test_user.id, True)
    
    # 获取KOL用户
    kol_users = await user_service.get_users(is_kol=True)
    assert all(u.is_kol for u in kol_users)
    assert any(u.id == test_user.id for u in kol_users)
    
    # 获取非KOL用户
    non_kol_users = await user_service.get_users(is_kol=False)
    assert all(not u.is_kol for u in non_kol_users)
    assert not any(u.id == test_user.id for u in non_kol_users)



# ==================== 关注功能测试 ====================

@pytest.fixture
async def test_user2(db_session: AsyncSession):
    """创建第二个测试用户"""
    user = User(
        id=str(uuid.uuid4()),
        employee_id="TEST003",
        name="测试用户2",
        department="技术部",
        position="工程师",
        is_kol=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_follow_user(user_service: UserService, test_user: User, test_user2: User):
    """测试关注用户"""
    follow = await user_service.follow_user(test_user.id, test_user2.id)
    
    assert follow.id is not None
    assert follow.follower_id == test_user.id
    assert follow.followee_id == test_user2.id


@pytest.mark.asyncio
async def test_follow_user_already_following(user_service: UserService, test_user: User, test_user2: User):
    """测试重复关注应该失败"""
    await user_service.follow_user(test_user.id, test_user2.id)
    
    with pytest.raises(HTTPException) as exc_info:
        await user_service.follow_user(test_user.id, test_user2.id)
    
    assert exc_info.value.status_code == 400
    assert "已经关注" in exc_info.value.detail


@pytest.mark.asyncio
async def test_follow_self(user_service: UserService, test_user: User):
    """测试不能关注自己"""
    with pytest.raises(HTTPException) as exc_info:
        await user_service.follow_user(test_user.id, test_user.id)
    
    assert exc_info.value.status_code == 400
    assert "不能关注自己" in exc_info.value.detail


@pytest.mark.asyncio
async def test_unfollow_user(user_service: UserService, test_user: User, test_user2: User):
    """测试取消关注用户"""
    await user_service.follow_user(test_user.id, test_user2.id)
    
    result = await user_service.unfollow_user(test_user.id, test_user2.id)
    
    assert result is True


@pytest.mark.asyncio
async def test_unfollow_user_not_following(user_service: UserService, test_user: User, test_user2: User):
    """测试取消未关注的用户应该失败"""
    with pytest.raises(HTTPException) as exc_info:
        await user_service.unfollow_user(test_user.id, test_user2.id)
    
    assert exc_info.value.status_code == 404
    assert "未关注" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_following_list(user_service: UserService, test_user: User, test_user2: User):
    """测试获取关注列表"""
    await user_service.follow_user(test_user.id, test_user2.id)
    
    following = await user_service.get_following_list(test_user.id)
    
    assert len(following) == 1
    assert following[0].id == test_user2.id


@pytest.mark.asyncio
async def test_get_followers_list(user_service: UserService, test_user: User, test_user2: User):
    """测试获取粉丝列表"""
    await user_service.follow_user(test_user.id, test_user2.id)
    
    followers = await user_service.get_followers_list(test_user2.id)
    
    assert len(followers) == 1
    assert followers[0].id == test_user.id


@pytest.mark.asyncio
async def test_is_following(user_service: UserService, test_user: User, test_user2: User):
    """测试检查是否已关注"""
    # 未关注时
    is_following = await user_service.is_following(test_user.id, test_user2.id)
    assert is_following is False
    
    # 关注后
    await user_service.follow_user(test_user.id, test_user2.id)
    is_following = await user_service.is_following(test_user.id, test_user2.id)
    assert is_following is True


@pytest.mark.asyncio
async def test_get_follow_counts(user_service: UserService, test_user: User, test_user2: User):
    """测试获取关注数和粉丝数"""
    await user_service.follow_user(test_user.id, test_user2.id)
    
    # 测试用户1的统计
    counts1 = await user_service.get_follow_counts(test_user.id)
    assert counts1["following_count"] == 1
    assert counts1["followers_count"] == 0
    
    # 测试用户2的统计
    counts2 = await user_service.get_follow_counts(test_user2.id)
    assert counts2["following_count"] == 0
    assert counts2["followers_count"] == 1


# ==================== 收藏功能测试 ====================

@pytest.fixture
async def test_content(db_session: AsyncSession, test_user: User):
    """创建测试内容"""
    from app.models.content import Content, ContentStatus
    
    content = Content(
        id=str(uuid.uuid4()),
        title="测试视频",
        description="这是一个测试视频",
        video_url="https://example.com/video.mp4",
        creator_id=test_user.id,
        status=ContentStatus.PUBLISHED,
        favorite_count=0,
        like_count=0
    )
    db_session.add(content)
    await db_session.commit()
    await db_session.refresh(content)
    return content


@pytest.mark.asyncio
async def test_favorite_content(user_service: UserService, test_user: User, test_content):
    """测试收藏内容"""
    favorite = await user_service.favorite_content(test_user.id, test_content.id)
    
    assert favorite.id is not None
    assert favorite.user_id == test_user.id
    assert favorite.content_id == test_content.id
    assert favorite.type.value == "favorite"


@pytest.mark.asyncio
async def test_favorite_content_idempotent(user_service: UserService, test_user: User, test_content):
    """测试收藏操作的幂等性"""
    favorite1 = await user_service.favorite_content(test_user.id, test_content.id)
    favorite2 = await user_service.favorite_content(test_user.id, test_content.id)
    
    # 应该返回相同的收藏记录
    assert favorite1.id == favorite2.id


@pytest.mark.asyncio
async def test_unfavorite_content(user_service: UserService, test_user: User, test_content):
    """测试取消收藏内容"""
    await user_service.favorite_content(test_user.id, test_content.id)
    
    result = await user_service.unfavorite_content(test_user.id, test_content.id)
    
    assert result is True


@pytest.mark.asyncio
async def test_unfavorite_content_not_favorited(user_service: UserService, test_user: User, test_content):
    """测试取消未收藏的内容应该失败"""
    with pytest.raises(HTTPException) as exc_info:
        await user_service.unfavorite_content(test_user.id, test_content.id)
    
    assert exc_info.value.status_code == 404
    assert "未收藏" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_favorite_list(user_service: UserService, test_user: User, test_content):
    """测试获取收藏列表"""
    await user_service.favorite_content(test_user.id, test_content.id)
    
    favorites = await user_service.get_favorite_list(test_user.id)
    
    assert len(favorites) == 1
    assert favorites[0].id == test_content.id


# ==================== 标记功能测试 ====================

@pytest.mark.asyncio
async def test_bookmark_content(user_service: UserService, test_user: User, test_content):
    """测试标记内容"""
    note = "这是一个重要的视频"
    bookmark = await user_service.bookmark_content(test_user.id, test_content.id, note)
    
    assert bookmark.id is not None
    assert bookmark.user_id == test_user.id
    assert bookmark.content_id == test_content.id
    assert bookmark.type.value == "bookmark"
    assert bookmark.note == note


@pytest.mark.asyncio
async def test_bookmark_content_without_note(user_service: UserService, test_user: User, test_content):
    """测试标记内容但不添加笔记"""
    bookmark = await user_service.bookmark_content(test_user.id, test_content.id)
    
    assert bookmark.note is None


@pytest.mark.asyncio
async def test_update_bookmark_note(user_service: UserService, test_user: User, test_content):
    """测试更新标记笔记"""
    await user_service.bookmark_content(test_user.id, test_content.id, "原始笔记")
    
    new_note = "更新后的笔记"
    updated_bookmark = await user_service.update_bookmark_note(test_user.id, test_content.id, new_note)
    
    assert updated_bookmark.note == new_note


@pytest.mark.asyncio
async def test_update_bookmark_note_not_bookmarked(user_service: UserService, test_user: User, test_content):
    """测试更新未标记内容的笔记应该失败"""
    with pytest.raises(HTTPException) as exc_info:
        await user_service.update_bookmark_note(test_user.id, test_content.id, "新笔记")
    
    assert exc_info.value.status_code == 404
    assert "未标记" in exc_info.value.detail


@pytest.mark.asyncio
async def test_delete_bookmark(user_service: UserService, test_user: User, test_content):
    """测试删除标记"""
    await user_service.bookmark_content(test_user.id, test_content.id, "测试笔记")
    
    result = await user_service.delete_bookmark(test_user.id, test_content.id)
    
    assert result is True


@pytest.mark.asyncio
async def test_delete_bookmark_not_bookmarked(user_service: UserService, test_user: User, test_content):
    """测试删除未标记的内容应该失败"""
    with pytest.raises(HTTPException) as exc_info:
        await user_service.delete_bookmark(test_user.id, test_content.id)
    
    assert exc_info.value.status_code == 404
    assert "未标记" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_bookmark_list(user_service: UserService, test_user: User, test_content):
    """测试获取标记列表"""
    note = "测试笔记"
    await user_service.bookmark_content(test_user.id, test_content.id, note)
    
    bookmarks = await user_service.get_bookmark_list(test_user.id)
    
    assert len(bookmarks) == 1
    assert bookmarks[0]["content"].id == test_content.id
    assert bookmarks[0]["note"] == note


# ==================== 点赞功能测试 ====================

@pytest.mark.asyncio
async def test_like_content(user_service: UserService, test_user: User, test_content):
    """测试点赞内容"""
    like = await user_service.like_content(test_user.id, test_content.id)
    
    assert like.id is not None
    assert like.user_id == test_user.id
    assert like.content_id == test_content.id
    assert like.type.value == "like"


@pytest.mark.asyncio
async def test_like_content_already_liked(user_service: UserService, test_user: User, test_content):
    """测试重复点赞应该失败"""
    await user_service.like_content(test_user.id, test_content.id)
    
    with pytest.raises(HTTPException) as exc_info:
        await user_service.like_content(test_user.id, test_content.id)
    
    assert exc_info.value.status_code == 400
    assert "已经点赞" in exc_info.value.detail


@pytest.mark.asyncio
async def test_unlike_content(user_service: UserService, test_user: User, test_content):
    """测试取消点赞内容"""
    await user_service.like_content(test_user.id, test_content.id)
    
    result = await user_service.unlike_content(test_user.id, test_content.id)
    
    assert result is True


@pytest.mark.asyncio
async def test_unlike_content_not_liked(user_service: UserService, test_user: User, test_content):
    """测试取消未点赞的内容应该失败"""
    with pytest.raises(HTTPException) as exc_info:
        await user_service.unlike_content(test_user.id, test_content.id)
    
    assert exc_info.value.status_code == 404
    assert "未点赞" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_like_list(user_service: UserService, test_user: User, test_content):
    """测试获取点赞列表"""
    await user_service.like_content(test_user.id, test_content.id)
    
    likes = await user_service.get_like_list(test_user.id)
    
    assert len(likes) == 1
    assert likes[0].id == test_content.id


@pytest.mark.asyncio
async def test_like_count_consistency(user_service: UserService, test_user: User, test_user2: User, test_content, db_session: AsyncSession):
    """测试点赞计数一致性"""
    from app.models.content import Content
    
    # 两个用户点赞
    await user_service.like_content(test_user.id, test_content.id)
    await user_service.like_content(test_user2.id, test_content.id)
    
    # 刷新内容对象
    await db_session.refresh(test_content)
    
    # 验证点赞计数
    assert test_content.like_count == 2
    
    # 取消一个点赞
    await user_service.unlike_content(test_user.id, test_content.id)
    await db_session.refresh(test_content)
    
    # 验证点赞计数更新
    assert test_content.like_count == 1
