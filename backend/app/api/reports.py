"""
举报相关API端点
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.models import get_db, User, ReportStatus
from app.schemas.report_schemas import (
    ReportCreate,
    ReportUpdate,
    ReportResponse,
    ReportListResponse,
    ReportStatistics
)
from app.services.report_service import ReportService
from app.utils.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["举报"])


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建举报
    
    - **content_id**: 被举报的内容ID
    - **reason**: 举报原因
    - **description**: 详细描述（可选）
    """
    try:
        report = await ReportService.create_report(
            db=db,
            report_data=report_data,
            reporter_id=current_user.id
        )
        return report
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建举报失败: {str(e)}"
        )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取举报详情
    
    - **report_id**: 举报ID
    """
    report = await ReportService.get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="举报记录不存在"
        )
    
    # 权限检查：只有举报人、管理员或处理人可以查看
    # TODO: 实现管理员权限检查
    if report.reporter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此举报记录"
        )
    
    return report


@router.get("", response_model=ReportListResponse)
async def list_reports(
    status_filter: Optional[ReportStatus] = Query(None, alias="status"),
    content_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查询举报列表
    
    - **status**: 举报状态筛选（可选）
    - **content_id**: 内容ID筛选（可选）
    - **page**: 页码
    - **page_size**: 每页数量
    """
    # TODO: 实现管理员权限检查
    # 普通用户只能查看自己的举报
    reports, total = await ReportService.list_reports(
        db=db,
        status=status_filter,
        content_id=content_id,
        reporter_id=current_user.id,  # 普通用户只能看自己的
        page=page,
        page_size=page_size
    )
    
    return ReportListResponse(
        reports=reports,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/me/reports", response_model=ReportListResponse)
async def get_my_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的举报记录
    
    - **page**: 页码
    - **page_size**: 每页数量
    """
    reports, total = await ReportService.get_user_reports(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )
    
    return ReportListResponse(
        reports=reports,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/content/{content_id}/reports", response_model=ReportListResponse)
async def get_content_reports(
    content_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取内容的举报记录（管理员使用）
    
    - **content_id**: 内容ID
    - **page**: 页码
    - **page_size**: 每页数量
    """
    # TODO: 实现管理员权限检查
    reports, total = await ReportService.get_content_reports(
        db=db,
        content_id=content_id,
        page=page,
        page_size=page_size
    )
    
    return ReportListResponse(
        reports=reports,
        total=total,
        page=page,
        page_size=page_size
    )


@router.put("/{report_id}", response_model=ReportResponse)
async def update_report_status(
    report_id: str,
    update_data: ReportUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新举报状态（管理员操作）
    
    - **report_id**: 举报ID
    - **status**: 新状态
    - **handler_note**: 处理备注（可选）
    """
    # TODO: 实现管理员权限检查
    # if not current_user.is_admin:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="需要管理员权限"
    #     )
    
    report = await ReportService.update_report_status(
        db=db,
        report_id=report_id,
        update_data=update_data,
        handler_id=current_user.id
    )
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="举报记录不存在"
        )
    
    return report


@router.get("/statistics/summary", response_model=ReportStatistics)
async def get_report_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取举报统计信息（管理员使用）
    """
    # TODO: 实现管理员权限检查
    # if not current_user.is_admin:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="需要管理员权限"
    #     )
    
    statistics = await ReportService.get_statistics(db)
    return statistics
