"""
用户相关API端点
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..schemas.user_schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
    LoginResponse,
    KOLStatusUpdate,
    AdminStatusUpdate,
    PasswordChangeRequest,
    FollowResponse,
    FollowCountsResponse,
    BookmarkRequest,
    BookmarkUpdateRequest,
    InteractionResponse
)
from ..services.user_service import UserService
from ..utils.auth import (
    create_access_token,
    get_current_active_user
)


router = APIRouter(prefix="/users", tags=["用户"])


def build_content_response(content):
    """
    构建ContentResponse，包含创作者信息
    
    Args:
        content: Content模型对象
        
    Returns:
        ContentResponse对象
    """
    from ..schemas.content_schemas import ContentResponse
    
    content_dict = {
        "id": content.id,
        "title": content.title,
        "description": content.description,
        "video_url": content.video_url,
        "cover_url": content.cover_url,
        "duration": content.duration,
        "file_size": content.file_size,
        "creator_id": content.creator_id,
        "status": content.status,
        "content_type": content.content_type,
        "view_count": content.view_count,
        "like_count": content.like_count,
        "favorite_count": content.favorite_count,
        "comment_count": content.comment_count,
        "share_count": content.share_count,
        "created_at": content.created_at,
        "updated_at": content.updated_at,
        "published_at": content.published_at,
    }
    
    # 添加创作者信息（如果已加载）
    if hasattr(content, 'creator') and content.creator:
        content_dict["creator"] = {
            "id": content.creator.id,
            "name": content.creator.name,
            "employee_id": content.creator.employee_id,
            "avatar_url": content.creator.avatar_url,
            "department": content.creator.department,
            "position": content.creator.position,
            "is_kol": content.creator.is_kol
        }
    
    return ContentResponse(**content_dict)


@router.post("/login", response_model=LoginResponse, summary="用户端登录")
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户端登录接口（C端用户使用）
    
    注：这是简化的登录实现，实际生产环境应该集成企业现有认证系统
    
    Args:
        login_data: 登录请求数据
        db: 数据库会话
        
    Returns:
        登录响应，包含访问令牌和用户信息
        
    Raises:
        HTTPException: 认证失败时抛出
    """
    user_service = UserService(db)
    
    # 认证用户
    user = await user_service.authenticate_user(login_data.employee_id, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败，员工ID或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 用户端登录：所有用户都可以登录
    # 创建访问令牌
    access_token = create_access_token(
        data={"sub": user.id, "employee_id": user.employee_id}
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/admin-login", response_model=LoginResponse, summary="管理后台登录")
async def admin_login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    管理后台登录接口
    
    只有 is_admin=True 的用户才能登录管理后台
    
    Args:
        login_data: 登录请求数据
        db: 数据库会话
        
    Returns:
        登录响应，包含访问令牌和用户信息
        
    Raises:
        HTTPException: 认证失败或权限不足时抛出
    """
    user_service = UserService(db)
    
    # 认证用户
    user = await user_service.authenticate_user(login_data.employee_id, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败，员工ID或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查管理员权限
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限才能登录管理后台"
        )
    
    # 创建访问令牌
    access_token = create_access_token(
        data={"sub": user.id, "employee_id": user.employee_id}
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="创建用户")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新用户
    
    Args:
        user_data: 用户创建数据
        db: 数据库会话
        
    Returns:
        创建的用户信息
    """
    user_service = UserService(db)
    user = await user_service.create_user(user_data)
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前登录用户的信息
    
    Args:
        current_user: 当前用户
        
    Returns:
        当前用户信息
    """
    return UserResponse.model_validate(current_user)


@router.get("/search", summary="搜索用户")
async def search_users(
    search: str = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    搜索用户（用于KOL候选人选择等场景）
    
    Args:
        search: 搜索关键词（姓名、员工ID）
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        
    Returns:
        用户列表
    """
    from sqlalchemy import select, or_, func
    
    query = select(User)
    
    # 搜索条件
    if search:
        query = query.filter(
            or_(
                User.name.like(f"%{search}%"),
                User.employee_id.like(f"%{search}%")
            )
        )
    
    # 总数
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0
    
    # 分页
    query = query.order_by(User.name).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return {
        "items": [UserResponse.model_validate(user) for user in users],
        "total": total
    }


@router.get("/experts", summary="获取专家列表")
async def get_experts(
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有专家（KOL）用户列表
    
    用于专家审核功能中选择专家
    
    Returns:
        专家用户列表
    """
    from sqlalchemy import select
    
    # 查询所有KOL用户作为专家
    result = await db.execute(
        select(User).where(User.is_kol == True).order_by(User.name)
    )
    experts = result.scalars().all()
    
    return {
        "items": [
            {
                "id": expert.id,
                "name": expert.name,
                "employee_id": expert.employee_id,
                "avatar_url": expert.avatar_url,
                "department": expert.department,
                "position": expert.position
            }
            for expert in experts
        ],
        "total": len(experts)
    }


@router.get("/{user_id}", response_model=UserResponse, summary="获取用户信息")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    根据用户ID获取用户信息
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        用户信息
        
    Raises:
        HTTPException: 用户不存在时抛出
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse, summary="更新当前用户信息")
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前登录用户的信息
    
    Args:
        user_data: 用户更新数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        更新后的用户信息
    """
    user_service = UserService(db)
    user = await user_service.update_user(current_user.id, user_data)
    return UserResponse.model_validate(user)


@router.post("/me/avatar", response_model=dict, summary="更新当前用户头像")
async def update_current_user_avatar(
    avatar: UploadFile = File(..., description="头像文件"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前登录用户的头像
    
    Args:
        avatar: 头像文件
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        包含头像URL的字典
    """
    user_service = UserService(db)
    avatar_url = await user_service.update_avatar(current_user.id, avatar)
    
    return {
        "avatar_url": avatar_url,
        "message": "头像更新成功"
    }


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户信息")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新指定用户的信息
    
    Args:
        user_id: 用户ID
        user_data: 用户更新数据
        db: 数据库会话
        
    Returns:
        更新后的用户信息
    """
    user_service = UserService(db)
    user = await user_service.update_user(user_id, user_data)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    删除指定用户
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        操作结果
    """
    user_service = UserService(db)
    await user_service.delete_user(user_id)
    return {"message": "删除用户成功"}


@router.put("/{user_id}/kol-status", response_model=UserResponse, summary="更新用户KOL状态")
async def update_user_kol_status(
    user_id: str,
    kol_data: KOLStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户的KOL状态
    
    注：管理后台功能，需要登录认证
    
    Args:
        user_id: 用户ID
        kol_data: KOL状态更新数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        更新后的用户信息
    """
    user_service = UserService(db)
    user = await user_service.update_kol_status(user_id, kol_data.is_kol)
    return UserResponse.model_validate(user)


@router.put("/{user_id}/admin-status", response_model=UserResponse, summary="更新用户管理员状态")
async def update_user_admin_status(
    user_id: str,
    admin_data: AdminStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户的管理员状态
    
    注：管理后台功能，需要登录认证
    
    Args:
        user_id: 用户ID
        admin_data: 管理员状态更新数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        更新后的用户信息
    """
    user_service = UserService(db)
    user = await user_service.update_admin_status(user_id, admin_data.is_admin)
    return UserResponse.model_validate(user)


@router.get("/", response_model=List[UserResponse], summary="获取用户列表")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    is_kol: bool = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        is_kol: 是否筛选KOL用户
        db: 数据库会话
        
    Returns:
        用户列表
    """
    user_service = UserService(db)
    users = await user_service.get_users(skip=skip, limit=limit, is_kol=is_kol)
    return [UserResponse.model_validate(user) for user in users]


@router.post("/sync/{employee_id}", response_model=UserResponse, summary="从企业系统同步用户")
async def sync_user(
    employee_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    从企业系统同步用户信息
    
    Args:
        employee_id: 员工ID
        db: 数据库会话
        
    Returns:
        同步后的用户信息
    """
    user_service = UserService(db)
    user = await user_service.sync_user_from_enterprise_system(employee_id)
    return UserResponse.model_validate(user)



# ==================== 关注功能API ====================

@router.post("/{user_id}/follow", response_model=FollowResponse, summary="关注用户")
async def follow_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    关注指定用户
    
    Args:
        user_id: 要关注的用户ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        关注关系信息
    """
    user_service = UserService(db)
    follow = await user_service.follow_user(current_user.id, user_id)
    return FollowResponse.model_validate(follow)


@router.delete("/{user_id}/follow", summary="取消关注用户")
async def unfollow_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    取消关注指定用户
    
    Args:
        user_id: 要取消关注的用户ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        操作结果
    """
    user_service = UserService(db)
    await user_service.unfollow_user(current_user.id, user_id)
    return {"message": "取消关注成功"}


@router.get("/me/following", response_model=List[UserResponse], summary="获取我的关注列表")
async def get_my_following(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的关注列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        关注的用户列表
    """
    user_service = UserService(db)
    users = await user_service.get_following_list(current_user.id, skip, limit)
    return [UserResponse.model_validate(user) for user in users]


@router.get("/{user_id}/following", response_model=List[UserResponse], summary="获取用户的关注列表")
async def get_user_following(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定用户的关注列表
    
    Args:
        user_id: 用户ID
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        
    Returns:
        关注的用户列表
    """
    user_service = UserService(db)
    users = await user_service.get_following_list(user_id, skip, limit)
    return [UserResponse.model_validate(user) for user in users]


@router.get("/me/followers", response_model=List[UserResponse], summary="获取我的粉丝列表")
async def get_my_followers(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的粉丝列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        粉丝用户列表
    """
    user_service = UserService(db)
    users = await user_service.get_followers_list(current_user.id, skip, limit)
    return [UserResponse.model_validate(user) for user in users]


@router.get("/{user_id}/followers", response_model=List[UserResponse], summary="获取用户的粉丝列表")
async def get_user_followers(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定用户的粉丝列表
    
    Args:
        user_id: 用户ID
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        
    Returns:
        粉丝用户列表
    """
    user_service = UserService(db)
    users = await user_service.get_followers_list(user_id, skip, limit)
    return [UserResponse.model_validate(user) for user in users]


@router.get("/me/following-feed", summary="获取关注用户的内容信息流")
async def get_following_feed(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取关注用户发布的内容信息流
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        关注用户发布的内容列表
    """
    from ..schemas.content_schemas import ContentResponse
    
    user_service = UserService(db)
    contents = await user_service.get_following_feed(current_user.id, skip, limit)
    return [build_content_response(content) for content in contents]


@router.get("/{user_id}/follow-status", summary="检查是否已关注用户")
async def check_follow_status(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    检查当前用户是否已关注指定用户
    
    Args:
        user_id: 用户ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        是否已关注
    """
    user_service = UserService(db)
    is_following = await user_service.is_following(current_user.id, user_id)
    return {"is_following": is_following}


@router.get("/{user_id}/follow-counts", response_model=FollowCountsResponse, summary="获取用户的关注数和粉丝数")
async def get_follow_counts(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定用户的关注数和粉丝数
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        关注数和粉丝数
    """
    user_service = UserService(db)
    counts = await user_service.get_follow_counts(user_id)
    return FollowCountsResponse(**counts)


# ==================== 收藏功能API ====================

@router.post("/contents/{content_id}/favorite", response_model=InteractionResponse, summary="收藏内容")
async def favorite_content(
    content_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    收藏指定内容
    
    Args:
        content_id: 内容ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        互动记录信息
    """
    user_service = UserService(db)
    favorite = await user_service.favorite_content(current_user.id, content_id)
    return InteractionResponse.model_validate(favorite)


@router.delete("/contents/{content_id}/favorite", summary="取消收藏内容")
async def unfavorite_content(
    content_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    取消收藏指定内容
    
    Args:
        content_id: 内容ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        操作结果
    """
    user_service = UserService(db)
    await user_service.unfavorite_content(current_user.id, content_id)
    return {"message": "取消收藏成功"}


@router.get("/me/favorites", summary="获取我的收藏列表")
async def get_my_favorites(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的收藏列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        收藏的内容列表
    """
    from ..schemas.content_schemas import ContentResponse
    
    user_service = UserService(db)
    contents = await user_service.get_favorite_list(current_user.id, skip, limit)
    return [build_content_response(content) for content in contents]


# ==================== 标记功能API ====================

@router.post("/contents/{content_id}/bookmark", response_model=InteractionResponse, summary="标记内容")
async def bookmark_content(
    content_id: str,
    bookmark_data: BookmarkRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    标记指定内容并添加笔记
    
    Args:
        content_id: 内容ID
        bookmark_data: 标记数据（包含笔记）
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        互动记录信息
    """
    user_service = UserService(db)
    bookmark = await user_service.bookmark_content(
        current_user.id,
        content_id,
        bookmark_data.note
    )
    return InteractionResponse.model_validate(bookmark)


@router.put("/contents/{content_id}/bookmark", response_model=InteractionResponse, summary="更新标记笔记")
async def update_bookmark(
    content_id: str,
    bookmark_data: BookmarkUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新标记的笔记内容
    
    Args:
        content_id: 内容ID
        bookmark_data: 标记更新数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        更新后的互动记录信息
    """
    user_service = UserService(db)
    bookmark = await user_service.update_bookmark_note(
        current_user.id,
        content_id,
        bookmark_data.note
    )
    return InteractionResponse.model_validate(bookmark)


@router.delete("/contents/{content_id}/bookmark", summary="删除标记")
async def delete_bookmark(
    content_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除指定内容的标记
    
    Args:
        content_id: 内容ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        操作结果
    """
    user_service = UserService(db)
    await user_service.delete_bookmark(current_user.id, content_id)
    return {"message": "删除标记成功"}


@router.get("/me/bookmarks", summary="获取我的标记列表")
async def get_my_bookmarks(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的标记列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        标记列表（包含内容和笔记）
    """
    from ..schemas.content_schemas import ContentResponse
    
    user_service = UserService(db)
    bookmarks = await user_service.get_bookmark_list(current_user.id, skip, limit)
    
    # 格式化返回数据
    result = []
    for bookmark in bookmarks:
        result.append({
            "content": build_content_response(bookmark["content"]),
            "note": bookmark["note"],
            "bookmarked_at": bookmark["bookmarked_at"]
        })
    
    return result


# ==================== 点赞功能API ====================

@router.post("/contents/{content_id}/like", response_model=InteractionResponse, summary="点赞内容")
async def like_content(
    content_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    点赞指定内容
    
    Args:
        content_id: 内容ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        互动记录信息
    """
    user_service = UserService(db)
    like = await user_service.like_content(current_user.id, content_id)
    return InteractionResponse.model_validate(like)


@router.delete("/contents/{content_id}/like", summary="取消点赞内容")
async def unlike_content(
    content_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    取消点赞指定内容
    
    Args:
        content_id: 内容ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        操作结果
    """
    user_service = UserService(db)
    await user_service.unlike_content(current_user.id, content_id)
    return {"message": "取消点赞成功"}


@router.get("/me/likes", summary="获取我的点赞列表")
async def get_my_likes(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的点赞列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        点赞的内容列表
    """
    from ..schemas.content_schemas import ContentResponse
    
    user_service = UserService(db)
    contents = await user_service.get_like_list(current_user.id, skip, limit)
    return [build_content_response(content) for content in contents]



# ==================== 用户活动历史API ====================

@router.get("/me/watch-history", summary="获取我的观看历史")
async def get_my_watch_history(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的观看历史
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        观看历史列表（包含内容和播放进度）
    """
    from ..schemas.content_schemas import ContentResponse
    
    user_service = UserService(db)
    history = await user_service.get_watch_history(current_user.id, skip, limit)
    
    # 格式化返回数据
    result = []
    for item in history:
        result.append({
            "content": build_content_response(item["content"]),
            "progress_seconds": item["progress_seconds"],
            "duration_seconds": item["duration_seconds"],
            "progress_percentage": item["progress_percentage"],
            "is_completed": item["is_completed"],
            "last_played_at": item["last_played_at"]
        })
    
    return result


@router.get("/me/downloads", summary="获取我的下载列表")
async def get_my_downloads(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的下载列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        下载列表（包含内容和下载信息）
    """
    from ..schemas.content_schemas import ContentResponse
    
    user_service = UserService(db)
    downloads = await user_service.get_download_list(current_user.id, skip, limit)
    
    # 格式化返回数据
    result = []
    for item in downloads:
        result.append({
            "content": build_content_response(item["content"]),
            "file_size": item["file_size"],
            "quality": item["quality"],
            "downloaded_at": item["downloaded_at"],
            "local_path": item["local_path"]
        })
    
    return result



# ==================== 创作者个人资料API ====================

@router.get("/{user_id}/profile", summary="获取创作者个人资料")
async def get_creator_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取创作者的详细个人资料
    
    Args:
        user_id: 创作者用户ID
        db: 数据库会话
        
    Returns:
        创作者资料信息，包括基本信息、统计数据等
        
    Raises:
        HTTPException: 创作者不存在时抛出
    """
    user_service = UserService(db)
    
    try:
        profile = await user_service.get_creator_profile(user_id)
        
        return {
            "user": UserResponse.model_validate(profile["user"]),
            "following_count": profile["following_count"],
            "followers_count": profile["followers_count"],
            "content_count": profile["content_count"],
            "total_views": profile["total_views"],
            "total_likes": profile["total_likes"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{user_id}/contents", summary="获取创作者的内容列表")
async def get_creator_contents(
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    获取创作者的发布内容列表
    
    Args:
        user_id: 创作者用户ID
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        
    Returns:
        创作者的内容列表
    """
    from ..schemas.content_schemas import ContentResponse
    
    user_service = UserService(db)
    contents = await user_service.get_creator_contents(user_id, skip, limit)
    
    return [build_content_response(content) for content in contents]


@router.post("/{user_id}/contact", summary="通过企业微信联系创作者")
async def contact_creator(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    通过企业微信联系创作者
    
    注：这是一个占位接口，实际实现需要集成企业微信API
    
    Args:
        user_id: 创作者用户ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        企业微信联系链接或操作结果
    """
    user_service = UserService(db)
    creator = await user_service.get_user_by_id(user_id)
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="创作者不存在"
        )
    
    # TODO: 集成企业微信API
    # 实际实现应该调用企业微信API打开与创作者的对话
    
    return {
        "success": True,
        "message": "企业微信联系功能待集成",
        "creator_name": creator.name,
        "creator_employee_id": creator.employee_id
    }


@router.post("/me/change-password", summary="修改当前用户密码")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改当前用户密码
    
    Args:
        password_data: 密码修改数据
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        成功消息
        
    Raises:
        HTTPException: 密码验证失败时抛出
    """
    # 验证新密码和确认密码是否一致
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码和确认密码不一致"
        )
    
    # 验证新密码不能与旧密码相同
    if password_data.old_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与旧密码相同"
        )
    
    user_service = UserService(db)
    
    # 修改密码
    await user_service.change_password(
        user_id=current_user.id,
        old_password=password_data.old_password,
        new_password=password_data.new_password
    )
    
    return {"message": "密码修改成功"}
