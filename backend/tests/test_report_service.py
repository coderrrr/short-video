"""
举报服务测试
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Report, ReportReason, ReportStatus, User, Content, ContentStatus
from app.services.report_service import ReportService
from app.schemas.report_schemas import ReportCreate, ReportUpdate
import uuid


@pytest.mark.asyncio
async def test_create_report(db_session: AsyncSession):
    """测试创建举报"""
    # 创建测试用户
    reporter = User(
        id=str(uuid.uuid4()),
        employee_id="TEST_REPORTER",
        name="测试举报人",
        department="测试部门",
        position="测试职位"
    )
    db_session.add(reporter)
    
    # 创建测试内容
    creator = User(
        id=str(uuid.uuid4()),
        employee_id="TEST_CREATOR",
        name="测试创作者",
        department="测试部门",
        position="测试职位"
    )
    db_session.add(creator)
    
    content = Content(
        id=str(uuid.uuid4()),
        title="测试内容",
        description="测试描述",
        video_url="https://example.com/video.mp4",
        creator_id=creator.id,
        status=ContentStatus.PUBLISHED
    )
    db_session.add(content)
    await db_session.commit()
    
    # 创建举报
    report_data = ReportCreate(
        content_id=content.id,
        reason=ReportReason.INAPPROPRIATE_CONTENT,
        description="这是不当内容"
    )
    
    report = await ReportService.create_report(
        db=db_session,
        report_data=report_data,
        reporter_id=reporter.id
    )
    
    # 验证
    assert report.id is not None
    assert report.content_id == content.id
    assert report.reporter_id == reporter.id
    assert report.reason == ReportReason.INAPPROPRIATE_CONTENT
    assert report.description == "这是不当内容"
    assert report.status == ReportStatus.PENDING


@pytest.mark.asyncio
async def test_create_duplicate_report(db_session: AsyncSession):
    """测试重复举报（应返回已存在的举报）"""
    # 创建测试数据
    reporter = User(
        id=str(uuid.uuid4()),
        employee_id="TEST_REPORTER2",
        name="测试举报人2",
        department="测试部门",
        position="测试职位"
    )
    db_session.add(reporter)
    
    creator = User(
        id=str(uuid.uuid4()),
        employee_id="TEST_CREATOR2",
        name="测试创作者2",
        department="测试部门",
        position="测试职位"
    )
    db_session.add(creator)
    
    content = Content(
        id=str(uuid.uuid4()),
        title="测试内容2",
        description="测试描述2",
        video_url="https://example.com/video2.mp4",
        creator_id=creator.id,
        status=ContentStatus.PUBLISHED
    )
    db_session.add(content)
    await db_session.commit()
    
    # 第一次举报
    report_data = ReportCreate(
        content_id=content.id,
        reason=ReportReason.SPAM,
        description="垃圾信息"
    )
    
    report1 = await ReportService.create_report(
        db=db_session,
        report_data=report_data,
        reporter_id=reporter.id
    )
    
    # 第二次举报（应返回相同的举报）
    report2 = await ReportService.create_report(
        db=db_session,
        report_data=report_data,
        reporter_id=reporter.id
    )
    
    # 验证返回的是同一个举报
    assert report1.id == report2.id


@pytest.mark.asyncio
async def test_get_report(db_session: AsyncSession):
    """测试获取举报详情"""
    # 创建测试数据
    reporter = User(
        id=str(uuid.uuid4()),
        employee_id="TEST_REPORTER3",
        name="测试举报人3",
        department="测试部门",
        position="测试职位"
    )
    db_session.add(reporter)
    
    creator = User(
        id=str(uuid.uuid4()),
        employee_id="TEST_CREATOR3",
        name="测试创作者3",
        department="测试部门",
        position="测试职位"
    )
    db_session.add(creator)
    
    content = Content(
        id=str(uuid.uuid4()),
        title="测试内容3",
        description="测试描述3",
        video_url="https://example.com/video3.mp4",
        creator_id=creator.id,
        status=ContentStatus.PUBLISHED
    )
    db_session.add(content)
    await db_session.commit()
    
    # 创建举报
    report_data = ReportCreate(
        content_id=content.id,
        reason=ReportReason.VIOLENCE,
        description="暴力内容"
    )
    
    created_report = await ReportService.create_report(
        db=db_session,
        report_data=report_data,
        reporter_id=reporter.id
    )
    
    # 获取举报
    fetched_report = await ReportService.get_report(db_session, created_report.id)
    
    # 验证
    assert fetched_report is not None
    assert fetched_report.id == created_report.id
    assert fetched_report.content_id == content.id
    assert fetched_report.reporter_id == reporter.id


@pytest.mark.asyncio
async def test_list_reports(db_session: AsyncSession):
    """测试查询举报列表"""
    # 创建测试数据
    reporter = User(
        id=str(uuid.uuid4()),
        employee_id="TEST_REPORTER4",
        name="测试举报人4",
        department="测试部门",
        position="测试职位"
    )
    db_session.add(reporter)
    
    creator = User(
        id=str(uuid.uuid4()),
        employee_id="TEST_CREATOR4",
        name="测试创作者4",
        department="测试部门",
        position="测试职位"
    )
    db_session.add(creator)
    
    # 创建多个内容和举报
    for i in range(3):
        content = Content(
            id=str(uuid.uuid4()),
            title=f"测试内容{i}",
            description=f"测试描述{i}",
            video_url=f"https://example.com/video{i}.mp4",
            creator_id=creator.id,
            status=ContentStatus.PUBLISHED
        )
        db_session.add(content)
        await db_session.commit()
        
        report_data = ReportCreate(
            content_id=content.id,
            reason=ReportReason.SPAM,
            description=f"举报{i}"
        )
        
        await ReportService.create_report(
            db=db_session,
            report_data=report_data,
            reporter_id=reporter.id
        )
    
    # 查询列表
    reports, total = await ReportService.list_reports(
        db=db_session,
        reporter_id=reporter.id,
        page=1,
        page_size=10
    )
    
    # 验证
    assert len(reports) == 3
    assert total == 3


@pytest.mark.asyncio
async def test_update_report_status(db_session: AsyncSession):
    """测试更新举报状态"""
    # 创建测试数据
    reporter = User(
        id=str(uuid.uuid4()),
        employee_id="TEST_REPORTER5",
        name="测试举报人5",
        department="测试部门",
        position="测试职位"
    )
    db_session.add(reporter)
    
    handler = User(
        id=str(uuid.uuid4()),
        employee_id="TEST_HANDLER",
        name="测试处理人",
        department="测试部门",
        position="管理员"
    )
    db_session.add(handler)
    
    creator = User(
        id=str(uuid.uuid4()),
        employee_id="TEST_CREATOR5",
        name="测试创作者5",
        department="测试部门",
        position="测试职位"
    )
    db_session.add(creator)
    
    content = Content(
        id=str(uuid.uuid4()),
        title="测试内容5",
        description="测试描述5",
        video_url="https://example.com/video5.mp4",
        creator_id=creator.id,
        status=ContentStatus.PUBLISHED
    )
    db_session.add(content)
    await db_session.commit()
    
    # 创建举报
    report_data = ReportCreate(
        content_id=content.id,
        reason=ReportReason.HARASSMENT,
        description="骚扰内容"
    )
    
    report = await ReportService.create_report(
        db=db_session,
        report_data=report_data,
        reporter_id=reporter.id
    )
    
    # 更新状态
    update_data = ReportUpdate(
        status=ReportStatus.RESOLVED,
        handler_note="已处理"
    )
    
    updated_report = await ReportService.update_report_status(
        db=db_session,
        report_id=report.id,
        update_data=update_data,
        handler_id=handler.id
    )
    
    # 验证
    assert updated_report is not None
    assert updated_report.status == ReportStatus.RESOLVED
    assert updated_report.handler_id == handler.id
    assert updated_report.handler_note == "已处理"
    assert updated_report.handled_at is not None


@pytest.mark.asyncio
async def test_get_statistics(db_session: AsyncSession):
    """测试获取举报统计"""
    # 创建测试数据
    reporter = User(
        id=str(uuid.uuid4()),
        employee_id="TEST_REPORTER6",
        name="测试举报人6",
        department="测试部门",
        position="测试职位"
    )
    db_session.add(reporter)
    
    creator = User(
        id=str(uuid.uuid4()),
        employee_id="TEST_CREATOR6",
        name="测试创作者6",
        department="测试部门",
        position="测试职位"
    )
    db_session.add(creator)
    
    # 创建不同状态的举报
    reasons = [ReportReason.SPAM, ReportReason.VIOLENCE, ReportReason.SPAM]
    for i, reason in enumerate(reasons):
        content = Content(
            id=str(uuid.uuid4()),
            title=f"测试内容{i}",
            description=f"测试描述{i}",
            video_url=f"https://example.com/video{i}.mp4",
            creator_id=creator.id,
            status=ContentStatus.PUBLISHED
        )
        db_session.add(content)
        await db_session.commit()
        
        report_data = ReportCreate(
            content_id=content.id,
            reason=reason,
            description=f"举报{i}"
        )
        
        await ReportService.create_report(
            db=db_session,
            report_data=report_data,
            reporter_id=reporter.id
        )
    
    # 获取统计
    stats = await ReportService.get_statistics(db_session)
    
    # 验证
    assert stats.total_reports >= 3
    assert stats.pending_reports >= 3
    assert ReportReason.SPAM.value in stats.reports_by_reason
    assert stats.reports_by_reason[ReportReason.SPAM.value] >= 2
