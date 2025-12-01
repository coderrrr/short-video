"""
审核工作流测试
"""
import pytest
import uuid
from datetime import datetime

from app.models.content import Content, ContentStatus
from app.models.user import User
from app.models.review_record import ReviewRecord
from app.services.content_service import ContentService


@pytest.mark.asyncio
async def test_approve_content(db_session):
    """
    测试批准内容
    
    需求：42.3
    """
    # 创建测试用户（创作者和审核员）
    creator = User(
        id=str(uuid.uuid4()),
        employee_id="TEST001",
        name="测试创作者",
        department="技术部",
        position="工程师"
    )
    reviewer = User(
        id=str(uuid.uuid4()),
        employee_id="ADMIN001",
        name="测试审核员",
        department="管理部",
        position="管理员"
    )
    db_session.add(creator)
    db_session.add(reviewer)
    await db_session.commit()
    
    # 创建测试内容（审核中状态）
    content = Content(
        id=str(uuid.uuid4()),
        title="测试视频",
        description="这是一个测试视频",
        video_url="https://example.com/test.mp4",
        creator_id=creator.id,
        status=ContentStatus.UNDER_REVIEW,
        content_type="工作知识"
    )
    db_session.add(content)
    await db_session.commit()
    
    # 批准内容
    content_service = ContentService(db_session)
    approved_content = await content_service.approve_content(
        content_id=content.id,
        reviewer_id=reviewer.id,
        comment="内容质量很好"
    )
    
    # 验证状态已更新
    assert approved_content.status == ContentStatus.PUBLISHED
    assert approved_content.published_at is not None
    
    # 验证审核记录已创建
    await db_session.refresh(content)
    review_records = content.review_records
    assert len(review_records) == 1
    assert review_records[0].status == "approved"
    assert review_records[0].reviewer_id == reviewer.id


@pytest.mark.asyncio
async def test_reject_content(db_session):
    """
    测试拒绝内容
    
    需求：42.4
    """
    # 创建测试用户
    creator = User(
        id=str(uuid.uuid4()),
        employee_id="TEST002",
        name="测试创作者2",
        department="技术部",
        position="工程师"
    )
    reviewer = User(
        id=str(uuid.uuid4()),
        employee_id="ADMIN002",
        name="测试审核员2",
        department="管理部",
        position="管理员"
    )
    db_session.add(creator)
    db_session.add(reviewer)
    await db_session.commit()
    
    # 创建测试内容
    content = Content(
        id=str(uuid.uuid4()),
        title="测试视频2",
        description="这是另一个测试视频",
        video_url="https://example.com/test2.mp4",
        creator_id=creator.id,
        status=ContentStatus.UNDER_REVIEW,
        content_type="生活分享"
    )
    db_session.add(content)
    await db_session.commit()
    
    # 拒绝内容
    content_service = ContentService(db_session)
    rejected_content = await content_service.reject_content(
        content_id=content.id,
        reviewer_id=reviewer.id,
        reason="内容不符合平台规范"
    )
    
    # 验证状态已更新
    assert rejected_content.status == ContentStatus.REJECTED
    assert rejected_content.published_at is None
    
    # 验证审核记录已创建
    await db_session.refresh(content)
    review_records = content.review_records
    assert len(review_records) == 1
    assert review_records[0].status == "rejected"
    assert review_records[0].reason == "内容不符合平台规范"


@pytest.mark.asyncio
async def test_approve_non_review_content_fails(db_session):
    """
    测试批准非审核中的内容应该失败
    
    需求：42.3
    """
    # 创建测试用户
    creator = User(
        id=str(uuid.uuid4()),
        employee_id="TEST003",
        name="测试创作者3",
        department="技术部",
        position="工程师"
    )
    reviewer = User(
        id=str(uuid.uuid4()),
        employee_id="ADMIN003",
        name="测试审核员3",
        department="管理部",
        position="管理员"
    )
    db_session.add(creator)
    db_session.add(reviewer)
    await db_session.commit()
    
    # 创建已发布的内容
    content = Content(
        id=str(uuid.uuid4()),
        title="已发布视频",
        description="这是一个已发布的视频",
        video_url="https://example.com/published.mp4",
        creator_id=creator.id,
        status=ContentStatus.PUBLISHED,
        content_type="工作知识"
    )
    db_session.add(content)
    await db_session.commit()
    
    # 尝试批准已发布的内容应该失败
    content_service = ContentService(db_session)
    with pytest.raises(ValueError, match="只能批准审核中的内容"):
        await content_service.approve_content(
            content_id=content.id,
            reviewer_id=reviewer.id
        )


@pytest.mark.asyncio
async def test_reject_without_reason_fails(db_session):
    """
    测试拒绝内容时不提供原因应该失败
    
    需求：42.4
    """
    # 创建测试用户
    creator = User(
        id=str(uuid.uuid4()),
        employee_id="TEST004",
        name="测试创作者4",
        department="技术部",
        position="工程师"
    )
    reviewer = User(
        id=str(uuid.uuid4()),
        employee_id="ADMIN004",
        name="测试审核员4",
        department="管理部",
        position="管理员"
    )
    db_session.add(creator)
    db_session.add(reviewer)
    await db_session.commit()
    
    # 创建测试内容
    content = Content(
        id=str(uuid.uuid4()),
        title="测试视频4",
        description="测试视频",
        video_url="https://example.com/test4.mp4",
        creator_id=creator.id,
        status=ContentStatus.UNDER_REVIEW,
        content_type="企业文化"
    )
    db_session.add(content)
    await db_session.commit()
    
    # 尝试拒绝但不提供原因应该失败
    content_service = ContentService(db_session)
    with pytest.raises(ValueError, match="拒绝原因不能为空"):
        await content_service.reject_content(
            content_id=content.id,
            reviewer_id=reviewer.id,
            reason=""
        )


@pytest.mark.asyncio
async def test_get_review_statistics(db_session):
    """
    测试获取审核统计信息
    
    需求：42.1
    """
    # 创建测试用户
    creator = User(
        id=str(uuid.uuid4()),
        employee_id="TEST005",
        name="测试创作者5",
        department="技术部",
        position="工程师"
    )
    reviewer = User(
        id=str(uuid.uuid4()),
        employee_id="ADMIN005",
        name="测试审核员5",
        department="管理部",
        position="管理员"
    )
    db_session.add(creator)
    db_session.add(reviewer)
    await db_session.commit()
    
    # 创建多个待审核内容
    for i in range(3):
        content = Content(
            id=str(uuid.uuid4()),
            title=f"待审核视频{i}",
            description=f"测试视频{i}",
            video_url=f"https://example.com/test{i}.mp4",
            creator_id=creator.id,
            status=ContentStatus.UNDER_REVIEW,
            content_type="工作知识"
        )
        db_session.add(content)
    
    await db_session.commit()
    
    # 获取统计信息
    content_service = ContentService(db_session)
    stats = await content_service.get_review_statistics()
    
    # 验证统计数据
    assert stats['pending_count'] >= 3
    assert 'today_count' in stats
    assert 'today_approved_count' in stats
    assert 'today_rejected_count' in stats
    assert 'by_content_type' in stats


@pytest.mark.asyncio
async def test_get_content_review_detail(db_session):
    """
    测试获取内容审核详情
    
    需求：42.2
    """
    # 创建测试用户
    creator = User(
        id=str(uuid.uuid4()),
        employee_id="TEST006",
        name="测试创作者6",
        department="技术部",
        position="工程师"
    )
    reviewer = User(
        id=str(uuid.uuid4()),
        employee_id="ADMIN006",
        name="测试审核员6",
        department="管理部",
        position="管理员"
    )
    db_session.add(creator)
    db_session.add(reviewer)
    await db_session.commit()
    
    # 创建测试内容
    content = Content(
        id=str(uuid.uuid4()),
        title="测试视频6",
        description="测试视频详情",
        video_url="https://example.com/test6.mp4",
        creator_id=creator.id,
        status=ContentStatus.UNDER_REVIEW,
        content_type="工作知识"
    )
    db_session.add(content)
    await db_session.commit()
    
    # 创建审核记录
    review_record = ReviewRecord(
        id=str(uuid.uuid4()),
        content_id=content.id,
        reviewer_id=reviewer.id,
        review_type="platform_review",
        status="pending",
        created_at=datetime.utcnow()
    )
    db_session.add(review_record)
    await db_session.commit()
    
    # 获取审核详情
    content_service = ContentService(db_session)
    detail = await content_service.get_content_review_detail(content.id)
    
    # 验证返回数据
    assert detail['content'].id == content.id
    assert len(detail['review_records']) == 1
    assert detail['review_records'][0]['reviewer_name'] == reviewer.name
