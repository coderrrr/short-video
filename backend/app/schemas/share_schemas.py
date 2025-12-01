"""
分享相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ShareLinkRequest(BaseModel):
    """生成分享链接请求"""
    content_id: str = Field(..., description="内容ID")
    platform: Optional[str] = Field("wechat", description="分享平台（wechat/link）")


class ShareLinkResponse(BaseModel):
    """分享链接响应"""
    share_url: str = Field(..., description="分享链接")
    content_id: str = Field(..., description="内容ID")
    title: str = Field(..., description="内容标题")
    description: Optional[str] = Field(None, description="内容描述")
    cover_url: Optional[str] = Field(None, description="封面图片URL")
    message: str = Field(..., description="响应消息")


class ShareRecordResponse(BaseModel):
    """分享记录响应"""
    id: str
    content_id: str
    user_id: str
    platform: str
    created_at: datetime
    
    class Config:
        from_attributes = True
