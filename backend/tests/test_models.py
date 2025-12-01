"""
测试数据模型
"""
import pytest
from app.models import (
    User,
    Content,
    ContentStatus,
    Tag,
    ContentTag,
    Interaction,
    InteractionType,
    Comment,
    ReviewRecord,
    Follow,
    Base
)


def test_import_models():
    """测试模型可以正确导入"""
    assert User is not None
    assert Content is not None
    assert ContentStatus is not None
    assert Tag is not None
    assert ContentTag is not None
    assert Interaction is not None
    assert InteractionType is not None
    assert Comment is not None
    assert ReviewRecord is not None
    assert Follow is not None
    assert Base is not None


def test_content_status_enum():
    """测试内容状态枚举"""
    assert ContentStatus.DRAFT == "draft"
    assert ContentStatus.UNDER_REVIEW == "under_review"
    assert ContentStatus.APPROVED == "approved"
    assert ContentStatus.REJECTED == "rejected"
    assert ContentStatus.PUBLISHED == "published"
    assert ContentStatus.REMOVED == "removed"


def test_interaction_type_enum():
    """测试互动类型枚举"""
    assert InteractionType.LIKE == "like"
    assert InteractionType.FAVORITE == "favorite"
    assert InteractionType.BOOKMARK == "bookmark"
    assert InteractionType.COMMENT == "comment"
    assert InteractionType.SHARE == "share"


def test_user_model_attributes():
    """测试用户模型属性"""
    # 验证User模型有必要的属性
    assert hasattr(User, 'id')
    assert hasattr(User, 'employee_id')
    assert hasattr(User, 'name')
    assert hasattr(User, 'avatar_url')
    assert hasattr(User, 'department')
    assert hasattr(User, 'position')
    assert hasattr(User, 'is_kol')
    assert hasattr(User, 'created_at')
    assert hasattr(User, 'updated_at')


def test_content_model_attributes():
    """测试内容模型属性"""
    # 验证Content模型有必要的属性
    assert hasattr(Content, 'id')
    assert hasattr(Content, 'title')
    assert hasattr(Content, 'description')
    assert hasattr(Content, 'video_url')
    assert hasattr(Content, 'cover_url')
    assert hasattr(Content, 'duration')
    assert hasattr(Content, 'file_size')
    assert hasattr(Content, 'creator_id')
    assert hasattr(Content, 'status')
    assert hasattr(Content, 'content_type')
    assert hasattr(Content, 'view_count')
    assert hasattr(Content, 'like_count')
    assert hasattr(Content, 'favorite_count')
    assert hasattr(Content, 'comment_count')
    assert hasattr(Content, 'share_count')
    assert hasattr(Content, 'created_at')
    assert hasattr(Content, 'updated_at')
    assert hasattr(Content, 'published_at')


def test_model_relationships():
    """测试模型关系"""
    # 验证关系定义存在
    assert hasattr(User, 'contents')
    assert hasattr(User, 'followers')
    assert hasattr(User, 'following')
    assert hasattr(Content, 'creator')
    assert hasattr(Content, 'tags')
    assert hasattr(Tag, 'children')
    assert hasattr(Tag, 'contents')
    assert hasattr(Comment, 'replies')
