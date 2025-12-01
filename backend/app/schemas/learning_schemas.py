"""
学习计划相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============ 专题 (Topic) ============

class TopicContentAssociation(BaseModel):
    """专题内容关联"""
    content_id: str
    order: int = 0


class TopicCreate(BaseModel):
    """创建专题"""
    name: str = Field(..., min_length=1, max_length=200, description="专题名称")
    description: Optional[str] = Field(None, description="专题描述")
    cover_url: Optional[str] = Field(None, description="专题封面图片URL")
    content_ids: List[str] = Field(default_factory=list, description="内容ID列表")


class TopicUpdate(BaseModel):
    """更新专题"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="专题名称")
    description: Optional[str] = Field(None, description="专题描述")
    cover_url: Optional[str] = Field(None, description="专题封面图片URL")
    is_active: Optional[bool] = Field(None, description="是否激活")


class TopicAddContent(BaseModel):
    """向专题添加内容"""
    content_ids: List[str] = Field(..., min_items=1, description="要添加的内容ID列表")


class TopicReorderContent(BaseModel):
    """重新排序专题内容"""
    content_orders: List[TopicContentAssociation] = Field(..., description="内容ID和顺序列表")


class TopicResponse(BaseModel):
    """专题响应"""
    id: str
    name: str
    description: Optional[str]
    cover_url: Optional[str]
    creator_id: str
    is_active: bool
    content_count: int
    view_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TopicDetailResponse(TopicResponse):
    """专题详情响应（包含内容列表）"""
    contents: List[dict] = Field(default_factory=list, description="内容列表")


# ============ 合集 (Collection) ============

class CollectionContentAssociation(BaseModel):
    """合集内容关联"""
    content_id: str
    order: int


class CollectionCreate(BaseModel):
    """创建合集"""
    name: str = Field(..., min_length=1, max_length=200, description="合集名称")
    description: Optional[str] = Field(None, description="合集描述")
    cover_url: Optional[str] = Field(None, description="合集封面图片URL")
    content_orders: List[CollectionContentAssociation] = Field(
        default_factory=list, 
        description="内容ID和顺序列表"
    )


class CollectionUpdate(BaseModel):
    """更新合集"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="合集名称")
    description: Optional[str] = Field(None, description="合集描述")
    cover_url: Optional[str] = Field(None, description="合集封面图片URL")
    is_active: Optional[bool] = Field(None, description="是否激活")


class CollectionAddContent(BaseModel):
    """向合集添加内容"""
    content_orders: List[CollectionContentAssociation] = Field(
        ..., 
        min_items=1, 
        description="要添加的内容ID和顺序列表"
    )


class CollectionReorderContent(BaseModel):
    """重新排序合集内容"""
    content_orders: List[CollectionContentAssociation] = Field(..., description="内容ID和顺序列表")


class CollectionResponse(BaseModel):
    """合集响应"""
    id: str
    name: str
    description: Optional[str]
    cover_url: Optional[str]
    creator_id: str
    is_active: bool
    content_count: int
    view_count: int
    completion_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CollectionDetailResponse(CollectionResponse):
    """合集详情响应（包含内容列表）"""
    contents: List[dict] = Field(default_factory=list, description="按顺序排列的内容列表")


# ============ 学习计划 (Learning Plan) ============

class LearningPlanResponse(BaseModel):
    """学习计划响应"""
    user_id: str
    recommended_topics: List[TopicResponse] = Field(default_factory=list)
    recommended_collections: List[CollectionResponse] = Field(default_factory=list)
    recommended_contents: List[dict] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


# ============ 学习进度 (Learning Progress) ============

class LearningProgressUpdate(BaseModel):
    """更新学习进度"""
    content_id: str
    completed: bool = Field(..., description="是否完成")
    progress_percentage: Optional[int] = Field(None, ge=0, le=100, description="进度百分比")


class LearningProgressResponse(BaseModel):
    """学习进度响应"""
    user_id: str
    total_watched: int = Field(0, description="总观看视频数")
    total_completed: int = Field(0, description="总完成视频数")
    total_watch_time: int = Field(0, description="总观看时间（秒）")
    completion_percentage: float = Field(0.0, description="完成百分比")
    
    class Config:
        from_attributes = True


class CollectionProgressResponse(BaseModel):
    """合集进度响应"""
    collection_id: str
    collection_name: str
    total_contents: int
    completed_contents: int
    completion_percentage: float
    
    class Config:
        from_attributes = True


class TopicProgressResponse(BaseModel):
    """专题进度响应"""
    topic_id: str
    topic_name: str
    total_contents: int
    completed_contents: int
    completion_percentage: float
    
    class Config:
        from_attributes = True


# ============ 学习提醒 (Learning Reminder) ============

class ReminderCreate(BaseModel):
    """创建学习提醒"""
    frequency: str = Field(..., description="提醒频率：daily, weekly, custom")
    time_of_day: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="提醒时间（HH:MM格式）")
    days_of_week: Optional[str] = Field(None, description="每周提醒日期（逗号分隔，如：1,3,5）")


class ReminderUpdate(BaseModel):
    """更新学习提醒"""
    enabled: Optional[bool] = Field(None, description="是否启用提醒")
    frequency: Optional[str] = Field(None, description="提醒频率：daily, weekly, custom")
    time_of_day: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$", description="提醒时间（HH:MM格式）")
    days_of_week: Optional[str] = Field(None, description="每周提醒日期（逗号分隔）")


class ReminderResponse(BaseModel):
    """学习提醒响应"""
    id: str
    user_id: str
    enabled: bool
    frequency: str
    time_of_day: Optional[str]
    days_of_week: Optional[str]
    next_reminder_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
