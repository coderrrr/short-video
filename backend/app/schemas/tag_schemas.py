"""
标签和分类相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TagBase(BaseModel):
    """标签基础模型"""
    name: str = Field(..., min_length=1, max_length=50, description="标签名称")
    category: Optional[str] = Field(None, max_length=50, description="标签分类")
    parent_id: Optional[str] = Field(None, description="父标签ID")


class TagCreate(TagBase):
    """创建标签请求"""
    pass


class TagUpdate(BaseModel):
    """更新标签请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="标签名称")
    category: Optional[str] = Field(None, max_length=50, description="标签分类")
    parent_id: Optional[str] = Field(None, description="父标签ID")


class TagResponse(TagBase):
    """标签响应"""
    id: str
    created_at: datetime
    children_count: Optional[int] = Field(0, description="子标签数量")
    content_count: Optional[int] = Field(0, description="关联内容数量")
    
    class Config:
        from_attributes = True


class TagTreeNode(TagResponse):
    """标签树节点"""
    children: List['TagTreeNode'] = Field(default_factory=list, description="子标签列表")


class TagListResponse(BaseModel):
    """标签列表响应"""
    tags: List[TagResponse]
    total: int
    page: int
    page_size: int


class CategoryBase(BaseModel):
    """分类基础模型（使用Tag实现）"""
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    parent_id: Optional[str] = Field(None, description="父分类ID")


class CategoryCreate(CategoryBase):
    """创建分类请求"""
    pass


class CategoryUpdate(BaseModel):
    """更新分类请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="分类名称")
    parent_id: Optional[str] = Field(None, description="父分类ID")


class CategoryResponse(BaseModel):
    """分类响应"""
    id: str
    name: str
    parent_id: Optional[str]
    created_at: datetime
    children_count: int = Field(0, description="子分类数量")
    content_count: int = Field(0, description="关联内容数量")
    
    class Config:
        from_attributes = True


class CategoryTreeNode(CategoryResponse):
    """分类树节点"""
    children: List['CategoryTreeNode'] = Field(default_factory=list, description="子分类列表")


class CategoryListResponse(BaseModel):
    """分类列表响应"""
    categories: List[CategoryResponse]
    total: int


class KOLBase(BaseModel):
    """KOL基础模型"""
    user_id: str = Field(..., description="用户ID")


class KOLCreate(KOLBase):
    """创建KOL请求"""
    pass


class KOLResponse(BaseModel):
    """KOL响应"""
    id: str
    employee_id: str
    name: str
    avatar_url: Optional[str]
    department: Optional[str]
    position: Optional[str]
    is_kol: bool
    created_at: datetime
    content_count: Optional[int] = Field(0, description="发布内容数量")
    follower_count: Optional[int] = Field(0, description="粉丝数量")
    
    class Config:
        from_attributes = True


class KOLListResponse(BaseModel):
    """KOL列表响应"""
    kols: List[KOLResponse]
    total: int
    page: int
    page_size: int


class BatchTagAssignRequest(BaseModel):
    """批量分配标签请求"""
    content_ids: List[str] = Field(..., description="内容ID列表")
    tag_ids: List[str] = Field(..., description="标签ID列表")


class BatchTagAssignResponse(BaseModel):
    """批量分配标签响应"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")


# 更新前向引用
TagTreeNode.model_rebuild()
CategoryTreeNode.model_rebuild()
