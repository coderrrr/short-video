"""
管理后台数据分析相关的Schema
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ContentPerformanceMetrics(BaseModel):
    """内容性能指标"""
    content_id: str
    title: str
    creator_name: str
    view_count: int = Field(description="观看次数")
    completion_count: int = Field(description="完播次数（观看至少90%）")
    unique_viewers: int = Field(description="独立观众数")
    like_count: int = Field(description="点赞数")
    favorite_count: int = Field(description="收藏数")
    comment_count: int = Field(description="评论数")
    share_count: int = Field(description="分享数")
    completion_rate: float = Field(description="完播率（完播次数/观看次数）")
    avg_watch_time: float = Field(description="平均观看时长（秒）")
    published_at: Optional[datetime] = Field(description="发布时间")
    
    class Config:
        from_attributes = True


class ContentAnalyticsSummary(BaseModel):
    """内容分析汇总"""
    total_contents: int = Field(description="总内容数")
    total_views: int = Field(description="总观看次数")
    total_completions: int = Field(description="总完播次数")
    avg_completion_rate: float = Field(description="平均完播率")
    total_likes: int = Field(description="总点赞数")
    total_favorites: int = Field(description="总收藏数")
    total_comments: int = Field(description="总评论数")
    total_shares: int = Field(description="总分享数")


class ContentAnalyticsListResponse(BaseModel):
    """内容分析列表响应"""
    summary: ContentAnalyticsSummary
    contents: List[ContentPerformanceMetrics]
    total: int
    page: int
    page_size: int


class ContentDetailedAnalytics(BaseModel):
    """内容详细分析"""
    content_id: str
    title: str
    description: Optional[str]
    creator_name: str
    creator_id: str
    duration: int = Field(description="视频时长（秒）")
    
    # 观看数据
    view_count: int
    completion_count: int
    unique_viewers: int
    completion_rate: float
    avg_watch_time: float
    avg_watch_percentage: float = Field(description="平均观看百分比")
    
    # 互动数据
    like_count: int
    favorite_count: int
    comment_count: int
    share_count: int
    
    # 时间数据
    created_at: datetime
    published_at: Optional[datetime]
    
    # 标签
    tags: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class InteractionRecord(BaseModel):
    """互动记录"""
    id: str
    user_id: str
    user_name: str
    content_id: str
    content_title: str
    interaction_type: str = Field(description="互动类型：like, favorite, bookmark")
    note: Optional[str] = Field(description="标记笔记（仅bookmark类型）")
    created_at: datetime
    
    class Config:
        from_attributes = True


class InteractionListResponse(BaseModel):
    """互动记录列表响应"""
    records: List[InteractionRecord]
    total: int
    page: int
    page_size: int


class CommentRecord(BaseModel):
    """评论记录"""
    id: str
    user_id: str
    user_name: str
    content_id: str
    content_title: str
    text: str
    parent_id: Optional[str] = Field(description="父评论ID（回复）")
    mentioned_users: List[str] = Field(default_factory=list, description="@提及的用户ID列表")
    created_at: datetime
    
    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """评论列表响应"""
    comments: List[CommentRecord]
    total: int
    page: int
    page_size: int


class ExportAnalyticsRequest(BaseModel):
    """导出分析报告请求"""
    content_ids: Optional[List[str]] = Field(default=None, description="要导出的内容ID列表，为空则导出所有")
    format: str = Field(default="csv", description="导出格式：csv 或 excel")
    include_detailed: bool = Field(default=False, description="是否包含详细数据")
