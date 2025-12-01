"""
举报服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime
import uuid
import logging

from app.models import Report, ReportReason, ReportStatus, Content, User
from app.schemas.report_schemas import (
    ReportCreate, 
    ReportUpdate, 
    ReportResponse,
    ReportStatistics
)

logger = logging.getLogger(__name__)


class ReportService:
    """举报服务类"""
    
    @staticmethod
    async def create_report(
        db: AsyncSession,
        report_data: ReportCreate,
        reporter_id: str
    ) -> Report:
        """
        创建举报记录
        
        Args:
            db: 数据库会话
            report_data: 举报数据
            reporter_id: 举报人ID
            
        Returns:
            创建的举报记录
            
        Raises:
            ValueError: 如果内容不存在
        """
        # 验证内容是否存在
        content_query = select(Content).where(Content.id == report_data.content_id)
        result = await db.execute(content_query)
        content = result.scalar_one_or_none()
        
        if not content:
            raise ValueError(f"内容不存在: {report_data.content_id}")
        
        # 检查是否已经举报过（同一用户对同一内容的待处理举报）
        existing_query = select(Report).where(
            and_(
                Report.content_id == report_data.content_id,
                Report.reporter_id == reporter_id,
                Report.status == ReportStatus.PENDING
            )
        )
        result = await db.execute(existing_query)
        existing_report = result.scalar_one_or_none()
        
        if existing_report:
            logger.info(f"用户 {reporter_id} 已经举报过内容 {report_data.content_id}")
            return existing_report
        
        # 创建举报记录
        report = Report(
            id=str(uuid.uuid4()),
            content_id=report_data.content_id,
            reporter_id=reporter_id,
            reason=report_data.reason,
            description=report_data.description,
            status=ReportStatus.PENDING
        )
        
        db.add(report)
        await db.commit()
        await db.refresh(report)
        
        logger.info(f"创建举报记录: {report.id}, 内容: {report_data.content_id}, 原因: {report_data.reason}")
        
        # TODO: 发送通知给管理员
        # await notification_service.notify_admins_new_report(report.id)
        
        return report
    
    @staticmethod
    async def get_report(
        db: AsyncSession,
        report_id: str
    ) -> Optional[Report]:
        """
        获取举报记录详情
        
        Args:
            db: 数据库会话
            report_id: 举报ID
            
        Returns:
            举报记录，如果不存在则返回None
        """
        query = select(Report).where(Report.id == report_id).options(
            selectinload(Report.content),
            selectinload(Report.reporter),
            selectinload(Report.handler)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_reports(
        db: AsyncSession,
        status: Optional[ReportStatus] = None,
        content_id: Optional[str] = None,
        reporter_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Report], int]:
        """
        查询举报记录列表
        
        Args:
            db: 数据库会话
            status: 举报状态筛选
            content_id: 内容ID筛选
            reporter_id: 举报人ID筛选
            page: 页码
            page_size: 每页数量
            
        Returns:
            (举报记录列表, 总数)
        """
        # 构建查询条件
        conditions = []
        if status:
            conditions.append(Report.status == status)
        if content_id:
            conditions.append(Report.content_id == content_id)
        if reporter_id:
            conditions.append(Report.reporter_id == reporter_id)
        
        # 查询总数
        count_query = select(func.count(Report.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        result = await db.execute(count_query)
        total = result.scalar()
        
        # 查询列表
        query = select(Report).options(
            selectinload(Report.content),
            selectinload(Report.reporter),
            selectinload(Report.handler)
        )
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Report.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        reports = result.scalars().all()
        
        return list(reports), total
    
    @staticmethod
    async def update_report_status(
        db: AsyncSession,
        report_id: str,
        update_data: ReportUpdate,
        handler_id: str
    ) -> Optional[Report]:
        """
        更新举报状态（管理员操作）
        
        Args:
            db: 数据库会话
            report_id: 举报ID
            update_data: 更新数据
            handler_id: 处理人ID
            
        Returns:
            更新后的举报记录，如果不存在则返回None
        """
        report = await ReportService.get_report(db, report_id)
        if not report:
            return None
        
        # 更新状态
        report.status = update_data.status
        report.handler_id = handler_id
        report.handler_note = update_data.handler_note
        report.handled_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(report)
        
        logger.info(f"更新举报状态: {report_id}, 新状态: {update_data.status}")
        
        # TODO: 发送通知给举报人
        # await notification_service.notify_reporter_result(report.id)
        
        return report
    
    @staticmethod
    async def get_user_reports(
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Report], int]:
        """
        获取用户的举报记录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            (举报记录列表, 总数)
        """
        return await ReportService.list_reports(
            db=db,
            reporter_id=user_id,
            page=page,
            page_size=page_size
        )
    
    @staticmethod
    async def get_content_reports(
        db: AsyncSession,
        content_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Report], int]:
        """
        获取内容的举报记录
        
        Args:
            db: 数据库会话
            content_id: 内容ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            (举报记录列表, 总数)
        """
        return await ReportService.list_reports(
            db=db,
            content_id=content_id,
            page=page,
            page_size=page_size
        )
    
    @staticmethod
    async def get_statistics(
        db: AsyncSession
    ) -> ReportStatistics:
        """
        获取举报统计信息
        
        Args:
            db: 数据库会话
            
        Returns:
            举报统计信息
        """
        # 总举报数
        total_query = select(func.count(Report.id))
        result = await db.execute(total_query)
        total_reports = result.scalar()
        
        # 待处理举报数
        pending_query = select(func.count(Report.id)).where(
            Report.status == ReportStatus.PENDING
        )
        result = await db.execute(pending_query)
        pending_reports = result.scalar()
        
        # 已处理举报数
        resolved_query = select(func.count(Report.id)).where(
            Report.status == ReportStatus.RESOLVED
        )
        result = await db.execute(resolved_query)
        resolved_reports = result.scalar()
        
        # 已驳回举报数
        rejected_query = select(func.count(Report.id)).where(
            Report.status == ReportStatus.REJECTED
        )
        result = await db.execute(rejected_query)
        rejected_reports = result.scalar()
        
        # 按原因统计
        reason_query = select(
            Report.reason,
            func.count(Report.id)
        ).group_by(Report.reason)
        result = await db.execute(reason_query)
        reports_by_reason = {
            reason.value: count for reason, count in result.all()
        }
        
        return ReportStatistics(
            total_reports=total_reports,
            pending_reports=pending_reports,
            resolved_reports=resolved_reports,
            rejected_reports=rejected_reports,
            reports_by_reason=reports_by_reason
        )
