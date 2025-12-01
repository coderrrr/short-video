"""
内容相关的Pydantic模型
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ContentStatus(str, Enum):
    """内容状态枚举"""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    REMOVED = "removed"


class VideoMetadataCreate(BaseModel):
    """创建视频元数据"""
    title: str = Field(..., min_length=1, max_length=200, description="视频标题")
    description: Optional[str] = Field(None, max_length=500, description="视频描述")
    content_type: str = Field(..., description="内容类型（工作知识、生活分享、企业文化等）")
    tags: List[str] = Field(default_factory=list, description="自定义标签")
    
    @validator('title')
    def title_not_empty(cls, v):
        """验证标题不为空"""
        if not v or not v.strip():
            raise ValueError('标题不能为空')
        return v.strip()
    
    @validator('description')
    def description_length(cls, v):
        """验证描述长度"""
        if v and len(v) > 500:
            raise ValueError('描述不能超过500个字符')
        return v


class VideoMetadataUpdate(BaseModel):
    """更新视频元数据"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="视频标题")
    description: Optional[str] = Field(None, max_length=500, description="视频描述")
    content_type: Optional[str] = Field(None, description="内容类型")
    tags: Optional[List[str]] = Field(None, description="自定义标签")
    cover_url: Optional[str] = Field(None, description="封面图片URL")
    
    @validator('title')
    def title_not_empty(cls, v):
        """验证标题不为空"""
        if v is not None and (not v or not v.strip()):
            raise ValueError('标题不能为空')
        return v.strip() if v else v
    
    @validator('description')
    def description_length(cls, v):
        """验证描述长度"""
        if v and len(v) > 500:
            raise ValueError('描述不能超过500个字符')
        return v


class FileUploadResponse(BaseModel):
    """文件上传响应（仅上传文件，不创建内容记录）"""
    url: str = Field(..., description="文件URL")
    filename: str = Field(..., description="原始文件名")
    size: int = Field(..., description="文件大小（字节）")
    content_type: str = Field(..., description="文件类型")


class VideoUploadResponse(BaseModel):
    """视频上传响应"""
    content_id: str = Field(..., description="内容ID")
    video_url: str = Field(..., description="视频URL")
    status: ContentStatus = Field(..., description="内容状态")
    message: str = Field(..., description="响应消息")


class ContentResponse(BaseModel):
    """内容响应"""
    id: str
    title: str
    description: Optional[str]
    video_url: str
    cover_url: Optional[str]
    duration: Optional[int]
    file_size: Optional[int]
    creator_id: str
    status: ContentStatus
    content_type: str
    view_count: int
    like_count: int
    favorite_count: int
    comment_count: int
    share_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    published_at: Optional[datetime]
    
    # 精选内容相关（管理后台功能）
    is_featured: Optional[int] = 0
    featured_priority: Optional[int] = 0
    featured_position: Optional[str] = None
    priority: Optional[int] = 0  # 前端兼容性：priority 是 featured_priority 的别名
    
    # 创作者信息（可选）
    creator: Optional[dict] = None
    
    # 用户互动状态（可选，需要登录用户才有）
    is_liked: Optional[bool] = False
    is_favorited: Optional[bool] = False
    is_bookmarked: Optional[bool] = False
    
    class Config:
        from_attributes = True


class CoverImageUploadResponse(BaseModel):
    """封面图片上传响应"""
    cover_url: str = Field(..., description="封面图片URL")
    message: str = Field(..., description="响应消息")


class VideoEditRequest(BaseModel):
    """视频编辑请求"""
    start_time: float = Field(..., ge=0, description="开始时间（秒）")
    end_time: float = Field(..., gt=0, description="结束时间（秒）")
    volume: float = Field(1.0, ge=0, le=2.0, description="音量（0-2倍）")
    
    @validator('end_time')
    def end_time_greater_than_start(cls, v, values):
        """验证结束时间大于开始时间"""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('结束时间必须大于开始时间')
        return v


class VideoFrameExtractRequest(BaseModel):
    """视频帧提取请求"""
    interval: int = Field(5, ge=1, le=30, description="提取间隔（秒）")


class ContentFilterRequest(BaseModel):
    """内容筛选请求"""
    content_type: Optional[List[str]] = Field(None, description="内容类型列表")
    position: Optional[List[str]] = Field(None, description="岗位列表")
    skill: Optional[List[str]] = Field(None, description="技能列表")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    creator_id: Optional[str] = Field(None, description="创作者ID")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


# ==================== 管理后台相关Schema ====================

class AdminContentFilterRequest(BaseModel):
    """管理员内容筛选请求"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    status: Optional[str] = Field(None, description="内容状态")
    content_type: Optional[str] = Field(None, description="内容类型")
    creator_id: Optional[str] = Field(None, description="创作者ID")
    search: Optional[str] = Field(None, description="搜索关键词")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")


class AdminContentListResponse(BaseModel):
    """管理员内容列表响应"""
    items: List[ContentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminBatchOperationRequest(BaseModel):
    """管理员批量操作请求"""
    operation_type: str = Field(..., description="操作类型（approve, reject, remove, feature, unfeature）")
    content_ids: List[str] = Field(..., min_items=1, description="内容ID列表")
    reason: Optional[str] = Field(None, description="操作原因（拒绝时必填）")
    
    @validator('operation_type')
    def validate_operation_type(cls, v):
        """验证操作类型"""
        allowed_types = ['approve', 'reject', 'remove', 'feature', 'unfeature']
        if v not in allowed_types:
            raise ValueError(f'操作类型必须是以下之一: {", ".join(allowed_types)}')
        return v
    
    @validator('reason')
    def reason_required_for_reject(cls, v, values):
        """拒绝操作时原因必填"""
        if 'operation_type' in values and values['operation_type'] == 'reject' and not v:
            raise ValueError('拒绝操作时必须提供原因')
        return v


class AdminBatchOperationResponse(BaseModel):
    """管理员批量操作响应"""
    success: List[str] = Field(..., description="成功的内容ID列表")
    failed: List[dict] = Field(..., description="失败的内容ID和原因")
    total: int = Field(..., description="总数")
    message: str = Field(..., description="操作结果消息")


class AdminContentUploadRequest(BaseModel):
    """管理员创建内容请求（文件已上传）"""
    video_url: str = Field(..., description="视频URL（已上传）")
    cover_url: Optional[str] = Field(None, description="封面URL（已上传）")
    title: str = Field(..., min_length=1, max_length=200, description="视频标题")
    description: Optional[str] = Field(None, max_length=500, description="视频描述")
    content_type: str = Field(..., description="内容类型")
    tag_ids: List[str] = Field(default_factory=list, description="标签ID列表")
    auto_publish: bool = Field(True, description="是否自动发布（跳过审核）")
    is_featured: bool = Field(False, description="是否精选")
    priority: int = Field(0, description="显示优先级")
    
    @validator('title')
    def title_not_empty(cls, v):
        """验证标题不为空"""
        if not v or not v.strip():
            raise ValueError('标题不能为空')
        return v.strip()


class AdminContentUpdateRequest(BaseModel):
    """管理员更新内容请求"""
    video_url: Optional[str] = Field(None, description="视频URL")
    cover_url: Optional[str] = Field(None, description="封面URL")
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="视频标题")
    description: Optional[str] = Field(None, max_length=500, description="视频描述")
    content_type: Optional[str] = Field(None, description="内容类型")
    tag_ids: Optional[List[str]] = Field(None, description="标签ID列表")
    is_featured: Optional[bool] = Field(None, description="是否精选")
    priority: Optional[int] = Field(None, description="显示优先级")
    
    @validator('title')
    def title_not_empty(cls, v):
        """验证标题不为空"""
        if v is not None and (not v or not v.strip()):
            raise ValueError('标题不能为空')
        return v.strip() if v else v


class AdminBatchUploadResponse(BaseModel):
    """管理员批量上传响应"""
    success: List[dict] = Field(..., description="成功上传的内容列表")
    failed: List[dict] = Field(..., description="失败的文件和原因")
    total: int = Field(..., description="总数")
    message: str = Field(..., description="上传结果消息")


class AdminContentRemoveRequest(BaseModel):
    """管理员删除内容请求"""
    content_ids: List[str] = Field(..., min_items=1, description="内容ID列表")
    reason: str = Field(..., min_length=1, description="删除原因")
    create_audit_log: bool = Field(True, description="是否创建审计日志")


class AdminFeatureContentRequest(BaseModel):
    """管理员精选内容请求"""
    content_id: str = Field(..., description="内容ID")
    is_featured: bool = Field(..., description="是否精选")
    priority: Optional[int] = Field(None, ge=1, le=100, description="显示优先级（1-100，数字越大优先级越高）")
    featured_position: Optional[str] = Field(None, description="精选位置（homepage, category_top等）")


class AdminContentStatistics(BaseModel):
    """管理员内容统计"""
    total_contents: int = Field(..., description="总内容数")
    draft_count: int = Field(..., description="草稿数")
    under_review_count: int = Field(..., description="审核中数")
    published_count: int = Field(..., description="已发布数")
    rejected_count: int = Field(..., description="已驳回数")
    removed_count: int = Field(..., description="已下架数")
    today_new_count: int = Field(..., description="今日新增数")
    today_published_count: int = Field(..., description="今日发布数")


# ==================== 审核相关Schema ====================

class ReviewQueueFilterRequest(BaseModel):
    """审核队列筛选请求"""
    content_type: Optional[str] = Field(None, description="内容类型筛选")
    creator_id: Optional[str] = Field(None, description="创作者ID筛选")
    start_date: Optional[str] = Field(None, description="开始日期（YYYY-MM-DD）")
    end_date: Optional[str] = Field(None, description="结束日期（YYYY-MM-DD）")


class ReviewQueueResponse(BaseModel):
    """审核队列响应"""
    items: List['ContentResponse']
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        from_attributes = True


class ContentApproveRequest(BaseModel):
    """批准内容请求"""
    content_id: str = Field(..., description="内容ID")
    comment: Optional[str] = Field(None, description="审核备注")


class ContentRejectRequest(BaseModel):
    """拒绝内容请求"""
    content_id: str = Field(..., description="内容ID")
    reason: str = Field(..., min_length=1, description="拒绝原因")
    
    @validator('reason')
    def reason_not_empty(cls, v):
        """验证拒绝原因不为空"""
        if not v or not v.strip():
            raise ValueError('拒绝原因不能为空')
        return v.strip()


class BatchReviewRequest(BaseModel):
    """批量审核请求"""
    content_ids: List[str] = Field(..., min_items=1, description="内容ID列表")
    action: str = Field(..., description="操作类型（approve或reject）")
    reason: Optional[str] = Field(None, description="拒绝原因（action为reject时必填）")
    
    @validator('action')
    def validate_action(cls, v):
        """验证操作类型"""
        if v not in ['approve', 'reject']:
            raise ValueError('操作类型必须是approve或reject')
        return v
    
    @validator('reason')
    def validate_reason(cls, v, values):
        """验证拒绝原因"""
        if values.get('action') == 'reject' and (not v or not v.strip()):
            raise ValueError('拒绝操作必须提供拒绝原因')
        return v


class BatchReviewResponse(BaseModel):
    """批量审核响应"""
    success: List[str] = Field(default_factory=list, description="成功的内容ID列表")
    failed: List[dict] = Field(default_factory=list, description="失败的内容列表")
    total: int = Field(..., description="总数")
    message: str = Field(..., description="操作结果消息")


class ReviewRecordResponse(BaseModel):
    """审核记录响应"""
    id: str
    content_id: str
    reviewer_id: str
    reviewer_name: Optional[str] = None
    review_type: str
    status: str
    reason: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ContentReviewDetailResponse(BaseModel):
    """内容审核详情响应"""
    content: 'ContentResponse'
    review_records: List[ReviewRecordResponse] = Field(default_factory=list)
    
    class Config:
        from_attributes = True
