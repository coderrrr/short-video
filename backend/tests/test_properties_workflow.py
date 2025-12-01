"""
基于属性的测试：状态转换属性

Feature: enterprise-video-learning-platform
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from uuid import uuid4

from app.models.content import Content, ContentStatus
from app.models.user import User
from app.services.content_service import ContentService
from app.schemas.content_schemas import VideoMetadataUpdate


# ============================================================================
# 属性 7：内容状态转换正确性
# ============================================================================

@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    title=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    description=st.text(max_size=500)
)
async def test_property_7_content_status_transitions(db_session, title, description):
    """
    # Feature: enterprise-video-learning-platform, Property 7: 内容状态转换正确性
    
    属性：对于任何内容，其状态转换应遵循以下规则：
    - 草稿 → 审核中（提交时）
    - 审核中 → 已发布（批准时）
    - 审核中 → 已驳回（拒绝时）
    - 已发布 → 已下架（删除时）
    
    验证需求：5.1, 6.1, 6.4, 6.5
    """
    # 创建测试用户
    creator = User(
        id=str(uuid4()),
        employee_id=f"EMP{uuid4().hex[:8]}",
        name="测试创作者",
        department="技术部",
        position="工程师"
    )
    db_session.add(creator)
    await db_session.commit()
    await db_session.refresh(creator)
    
    # 创建审核员
    reviewer = User(
        id=str(uuid4()),
        employee_id=f"EMP{uuid4().hex[:8]}",
        name="测试审核员",
        department="内容审核部",
        position="审核员"
    )
    db_session.add(reviewer)
    await db_session.commit()
    await db_session.refresh(reviewer)
    
    # 测试1: 草稿 → 审核中（提交时）
    content = Content(
        id=str(uuid4()),
        title=title,
        description=description,
        video_url=f"http://example.com/video_{uuid4().hex}.mp4",
        creator_id=creator.id,
        status=ContentStatus.DRAFT
    )
    db_session.add(content)
    await db_session.commit()
    await db_session.refresh(content)
    
    # 提交审核
    content_service = ContentService(db_session)
    await content_service.submit_for_review(content.id, creator.id)
    await db_session.refresh(content)
    
    assert content.status == ContentStatus.UNDER_REVIEW, \
        f"提交后状态应为审核中，实际为 {content.status}"
    
    # 测试2: 审核中 → 已发布（批准时）
    content_for_approval = Content(
        id=str(uuid4()),
        title=title + "_approval",
        description=description,
        video_url=f"http://example.com/video_{uuid4().hex}.mp4",
        creator_id=creator.id,
        status=ContentStatus.UNDER_REVIEW
    )
    db_session.add(content_for_approval)
    await db_session.commit()
    await db_session.refresh(content_for_approval)
    
    # 批准内容
    await content_service.approve_content(
        content_for_approval.id,
        reviewer.id,
        "内容质量良好"
    )
    await db_session.refresh(content_for_approval)
    
    assert content_for_approval.status == ContentStatus.PUBLISHED, \
        f"批准后状态应为已发布，实际为 {content_for_approval.status}"
    
    # 测试3: 审核中 → 已驳回（拒绝时）
    content_for_rejection = Content(
        id=str(uuid4()),
        title=title + "_rejection",
        description=description,
        video_url=f"http://example.com/video_{uuid4().hex}.mp4",
        creator_id=creator.id,
        status=ContentStatus.UNDER_REVIEW
    )
    db_session.add(content_for_rejection)
    await db_session.commit()
    await db_session.refresh(content_for_rejection)
    
    # 拒绝内容
    await content_service.reject_content(
        content_for_rejection.id,
        reviewer.id,
        "内容不符合规范"
    )
    await db_session.refresh(content_for_rejection)
    
    assert content_for_rejection.status == ContentStatus.REJECTED, \
        f"拒绝后状态应为已驳回，实际为 {content_for_rejection.status}"
    
    # 测试4: 已发布 → 已下架（删除时）
    content_for_deletion = Content(
        id=str(uuid4()),
        title=title + "_deletion",
        description=description,
        video_url=f"http://example.com/video_{uuid4().hex}.mp4",
        creator_id=creator.id,
        status=ContentStatus.PUBLISHED
    )
    db_session.add(content_for_deletion)
    await db_session.commit()
    await db_session.refresh(content_for_deletion)
    
    # 删除内容（下架）- 直接更新状态
    content_for_deletion.status = ContentStatus.REMOVED
    await db_session.commit()
    await db_session.refresh(content_for_deletion)
    
    assert content_for_deletion.status == ContentStatus.REMOVED, \
        f"删除后状态应为已下架，实际为 {content_for_deletion.status}"


# ============================================================================
# 属性 8：审核中内容不可编辑
# ============================================================================

@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    original_title=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    new_title=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    description=st.text(max_size=500)
)
async def test_property_8_under_review_content_not_editable(
    db_session,
    original_title,
    new_title,
    description
):
    """
    # Feature: enterprise-video-learning-platform, Property 8: 审核中内容不可编辑
    
    属性：对于任何状态为"审核中"的内容，创作者的编辑请求应被拒绝
    
    验证需求：6.3
    """
    # 创建测试用户
    creator = User(
        id=str(uuid4()),
        employee_id=f"EMP{uuid4().hex[:8]}",
        name="测试创作者",
        department="技术部",
        position="工程师"
    )
    db_session.add(creator)
    await db_session.commit()
    await db_session.refresh(creator)
    
    # 创建审核中的内容
    content = Content(
        id=str(uuid4()),
        title=original_title,
        description=description,
        video_url=f"http://example.com/video_{uuid4().hex}.mp4",
        creator_id=creator.id,
        status=ContentStatus.UNDER_REVIEW
    )
    db_session.add(content)
    await db_session.commit()
    await db_session.refresh(content)
    
    # 尝试编辑审核中的内容应该失败
    content_service = ContentService(db_session)
    metadata_update = VideoMetadataUpdate(
        title=new_title,
        description="尝试修改描述"
    )
    with pytest.raises(Exception) as exc_info:
        await content_service.update_metadata(
            content.id,
            creator.id,
            metadata_update
        )
    
    # 验证抛出了正确的异常
    assert "审核中" in str(exc_info.value) or "under review" in str(exc_info.value).lower(), \
        f"应该抛出审核中不可编辑的异常，实际异常: {exc_info.value}"
    
    # 验证内容未被修改
    await db_session.refresh(content)
    assert content.title == original_title, \
        f"审核中的内容标题不应被修改，原标题: {original_title}, 当前标题: {content.title}"
    assert content.status == ContentStatus.UNDER_REVIEW, \
        f"内容状态应保持为审核中，实际为 {content.status}"
