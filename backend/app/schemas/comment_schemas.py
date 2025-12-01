"""
评论相关的Pydantic模型
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime


class CommentCreate(BaseModel):
    """创建评论请求"""
    content_id: str = Field(..., description="内容ID")
    text: str = Field(..., min_length=1, max_length=1000, description="评论文本")
    parent_id: Optional[str] = Field(None, description="父评论ID（回复评论时使用）")
    mentioned_users: Optional[List[str]] = Field(default_factory=list, description="@提及的用户ID列表")
    
    @validator('text')
    def validate_text(cls, v):
        """验证评论文本不为空"""
        if not v or not v.strip():
            raise ValueError('评论内容不能为空')
        return v.strip()


class CommentUpdate(BaseModel):
    """更新评论请求"""
    text: str = Field(..., min_length=1, max_length=1000, description="评论文本")
    
    @validator('text')
    def validate_text(cls, v):
        """验证评论文本不为空"""
        if not v or not v.strip():
            raise ValueError('评论内容不能为空')
        return v.strip()


class UserBrief(BaseModel):
    """用户简要信息"""
    id: str
    name: str
    avatar_url: Optional[str] = None
    is_kol: bool = False
    
    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    """评论响应"""
    id: str
    content_id: str
    user_id: str
    user: Optional[UserBrief] = None
    text: str
    parent_id: Optional[str] = None
    mentioned_users: Optional[List[str]] = None
    reply_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """评论列表响应"""
    comments: List[CommentResponse]
    total: int
    page: int
    page_size: int
