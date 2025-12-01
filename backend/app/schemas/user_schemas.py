"""
用户相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模型"""
    employee_id: str = Field(..., description="员工ID")
    name: str = Field(..., description="姓名")
    department: Optional[str] = Field(None, description="部门")
    position: Optional[str] = Field(None, description="岗位")


class UserCreate(UserBase):
    """创建用户模型"""
    password: str = Field(..., description="密码")


class UserUpdate(BaseModel):
    """更新用户模型"""
    name: Optional[str] = Field(None, description="姓名")
    department: Optional[str] = Field(None, description="部门")
    position: Optional[str] = Field(None, description="岗位")
    avatar_url: Optional[str] = Field(None, description="头像URL")


class UserResponse(UserBase):
    """用户响应模型"""
    id: str = Field(..., description="用户ID")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    is_kol: bool = Field(False, description="是否为KOL")
    is_admin: bool = Field(False, description="是否为管理员")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """登录请求模型"""
    employee_id: str = Field(..., description="员工ID")
    password: str = Field(..., description="密码")
    # 注：实际生产环境应该集成企业现有认证系统
    # 这里简化处理，仅用于开发测试


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    user: UserResponse = Field(..., description="用户信息")


class TokenData(BaseModel):
    """Token数据模型"""
    user_id: Optional[str] = None
    employee_id: Optional[str] = None


class KOLStatusUpdate(BaseModel):
    """KOL状态更新模型"""
    is_kol: bool = Field(..., description="是否为KOL")


class AdminStatusUpdate(BaseModel):
    """管理员状态更新模型"""
    is_admin: bool = Field(..., description="是否为管理员")


class PasswordChangeRequest(BaseModel):
    """修改密码请求模型"""
    old_password: str = Field(..., description="旧密码", min_length=6)
    new_password: str = Field(..., description="新密码", min_length=6)
    confirm_password: str = Field(..., description="确认新密码", min_length=6)


# ==================== 关注相关模型 ====================

class FollowResponse(BaseModel):
    """关注响应模型"""
    id: str = Field(..., description="关注关系ID")
    follower_id: str = Field(..., description="关注者ID")
    followee_id: str = Field(..., description="被关注者ID")
    created_at: datetime = Field(..., description="关注时间")
    
    class Config:
        from_attributes = True


class FollowCountsResponse(BaseModel):
    """关注数统计响应模型"""
    following_count: int = Field(..., description="关注数")
    followers_count: int = Field(..., description="粉丝数")


# ==================== 互动相关模型 ====================

class BookmarkRequest(BaseModel):
    """标记请求模型"""
    note: Optional[str] = Field(None, description="笔记内容")


class BookmarkUpdateRequest(BaseModel):
    """标记更新请求模型"""
    note: str = Field(..., description="笔记内容")


class InteractionResponse(BaseModel):
    """互动响应模型"""
    id: str = Field(..., description="互动记录ID")
    user_id: str = Field(..., description="用户ID")
    content_id: str = Field(..., description="内容ID")
    type: str = Field(..., description="互动类型")
    note: Optional[str] = Field(None, description="笔记内容（仅标记类型）")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True
