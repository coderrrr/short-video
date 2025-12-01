"""
举报相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.report import ReportReason, ReportStatus


class ReportCreate(BaseModel):
    """创建举报请求"""
    content_id: str = Field(..., description="被举报的内容ID")
    reason: ReportReason = Field(..., description="举报原因")
    description: Optional[str] = Field(None, max_length=500, description="详细描述")


class ReportUpdate(BaseModel):
    """更新举报状态请求（管理员使用）"""
    status: ReportStatus = Field(..., description="举报状态")
    handler_note: Optional[str] = Field(None, max_length=500, description="处理备注")


class ReportResponse(BaseModel):
    """举报响应"""
    id: str
    content_id: str
    reporter_id: str
    reason: ReportReason
    description: Optional[str]
    status: ReportStatus
    handler_id: Optional[str]
    handler_note: Optional[str]
    handled_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """举报列表响应"""
    reports: list[ReportResponse]
    total: int
    page: int
    page_size: int


class ReportStatistics(BaseModel):
    """举报统计"""
    total_reports: int
    pending_reports: int
    resolved_reports: int
    rejected_reports: int
    reports_by_reason: dict[str, int]
