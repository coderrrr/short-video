"""
用户服务
"""
import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func
from fastapi import HTTPException, status, UploadFile

from ..models.user import User
from ..models.follow import Follow
from ..models.interaction import Interaction, InteractionType
from ..models.content import Content, ContentStatus
from ..schemas.user_schemas import UserCreate, UserUpdate, UserResponse
from ..services.storage import get_storage


class UserService:
    """用户服务类"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化用户服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.storage_service = get_storage()
    
    async def get_user_by_id(self, user_id: str, include_deleted: bool = False) -> Optional[User]:
        """
        根据ID获取用户
        
        Args:
            user_id: 用户ID
            include_deleted: 是否包含已删除的用户
            
        Returns:
            用户对象，如果不存在则返回None
        """
        query = select(User).where(User.id == user_id)
        
        # 默认不包含已删除的用户
        if not include_deleted:
            query = query.where(User.is_deleted == False)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_by_employee_id(self, employee_id: str, include_deleted: bool = False) -> Optional[User]:
        """
        根据员工ID获取用户
        
        Args:
            employee_id: 员工ID
            include_deleted: 是否包含已删除的用户
            
        Returns:
            用户对象，如果不存在则返回None
        """
        query = select(User).where(User.employee_id == employee_id)
        
        # 默认不包含已删除的用户
        if not include_deleted:
            query = query.where(User.is_deleted == False)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        创建新用户
        
        Args:
            user_data: 用户创建数据
            
        Returns:
            创建的用户对象
            
        Raises:
            HTTPException: 员工ID已存在时抛出
        """
        # 检查员工ID是否已存在
        existing_user = await self.get_user_by_employee_id(user_data.employee_id)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"员工ID {user_data.employee_id} 已存在"
            )
        
        # 对密码进行哈希处理
        from ..utils.auth import get_password_hash
        password_hash = get_password_hash(user_data.password)
        
        # 创建新用户
        user = User(
            id=str(uuid.uuid4()),
            employee_id=user_data.employee_id,
            name=user_data.name,
            department=user_data.department,
            position=user_data.position,
            password_hash=password_hash,
            is_kol=False
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            user_data: 用户更新数据
            
        Returns:
            更新后的用户对象
            
        Raises:
            HTTPException: 用户不存在时抛出
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新字段
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        """
        软删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功删除
            
        Raises:
            HTTPException: 用户不存在时抛出
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 检查是否已删除
        if user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已被删除"
            )
        
        # 软删除用户
        from datetime import datetime
        user.is_deleted = True
        user.deleted_at = datetime.utcnow()
        
        await self.db.commit()
        
        return True
    
    async def update_avatar(self, user_id: str, avatar_file: UploadFile) -> str:
        """
        更新用户头像
        
        Args:
            user_id: 用户ID
            avatar_file: 头像文件
            
        Returns:
            头像URL
            
        Raises:
            HTTPException: 用户不存在或文件格式不支持时抛出
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 验证文件格式
        allowed_formats = ["jpg", "jpeg", "png", "gif"]
        file_extension = avatar_file.filename.split(".")[-1].lower()
        
        if file_extension not in allowed_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的图片格式，请上传 {', '.join(allowed_formats)} 格式的图片"
            )
        
        # 上传头像到存储服务
        object_key = f"avatars/{user_id}.{file_extension}"
        avatar_url = await self.storage_service.upload_file(
            file=avatar_file.file,
            object_key=object_key,
            content_type=avatar_file.content_type
        )
        
        # 更新用户头像URL
        user.avatar_url = avatar_url
        await self.db.commit()
        await self.db.refresh(user)
        
        return avatar_url
    
    async def update_kol_status(self, user_id: str, is_kol: bool) -> User:
        """
        更新用户KOL状态
        
        Args:
            user_id: 用户ID
            is_kol: 是否为KOL
            
        Returns:
            更新后的用户对象
            
        Raises:
            HTTPException: 用户不存在时抛出
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        user.is_kol = is_kol
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update_admin_status(self, user_id: str, is_admin: bool) -> User:
        """
        更新用户管理员状态
        
        Args:
            user_id: 用户ID
            is_admin: 是否为管理员
            
        Returns:
            更新后的用户对象
            
        Raises:
            HTTPException: 用户不存在时抛出
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        user.is_admin = is_admin
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def sync_user_from_enterprise_system(self, employee_id: str) -> User:
        """
        从企业系统同步用户信息
        
        注：这是一个占位方法，实际实现需要集成企业现有认证系统
        
        Args:
            employee_id: 员工ID
            
        Returns:
            同步后的用户对象
            
        Raises:
            HTTPException: 无法从企业系统获取用户信息时抛出
        """
        # TODO: 实际实现需要调用企业系统API获取用户信息
        # 这里仅作为示例，返回现有用户或创建新用户
        
        user = await self.get_user_by_employee_id(employee_id)
        
        if not user:
            # 如果用户不存在，从企业系统获取信息并创建
            # 这里简化处理，实际应该调用企业系统API
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"无法从企业系统获取员工 {employee_id} 的信息"
            )
        
        # 这里可以添加从企业系统更新用户信息的逻辑
        # 例如：更新部门、岗位等信息
        
        return user
    
    async def authenticate_user(self, employee_id: str, password: str) -> Optional[User]:
        """
        认证用户
        
        注：这是简化的认证方法，实际生产环境应该集成企业现有认证系统
        
        Args:
            employee_id: 员工ID
            password: 密码
            
        Returns:
            认证成功的用户对象，失败返回None
        """
        # 实际生产环境应该：
        # 1. 调用企业SSO/LDAP/AD等认证系统
        # 2. 验证用户凭据
        # 3. 同步用户信息
        
        # 获取用户
        user = await self.get_user_by_employee_id(employee_id)
        
        if not user:
            # 如果用户不存在，尝试从企业系统同步
            try:
                user = await self.sync_user_from_enterprise_system(employee_id)
            except HTTPException:
                return None
        
        # 验证密码
        if not user.password_hash:
            # 如果用户没有设置密码，拒绝登录
            return None
        
        from ..utils.auth import verify_password
        if not verify_password(password, user.password_hash):
            # 密码不匹配
            return None
        
        return user
    
    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_kol: Optional[bool] = None,
        include_deleted: bool = False
    ) -> List[User]:
        """
        获取用户列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            is_kol: 是否筛选KOL用户
            include_deleted: 是否包含已删除的用户
            
        Returns:
            用户列表
        """
        query = select(User)
        
        # 默认不包含已删除的用户
        if not include_deleted:
            query = query.where(User.is_deleted == False)
        
        if is_kol is not None:
            query = query.where(User.is_kol == is_kol)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    # ==================== 关注功能 ====================
    
    async def follow_user(self, follower_id: str, followee_id: str) -> Follow:
        """
        关注用户
        
        Args:
            follower_id: 关注者ID
            followee_id: 被关注者ID
            
        Returns:
            关注关系对象
            
        Raises:
            HTTPException: 用户不存在或已关注时抛出
        """
        # 验证用户存在
        follower = await self.get_user_by_id(follower_id)
        if not follower:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="关注者不存在"
            )
        
        followee = await self.get_user_by_id(followee_id)
        if not followee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="被关注者不存在"
            )
        
        # 不能关注自己
        if follower_id == followee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能关注自己"
            )
        
        # 检查是否已关注
        existing_follow = await self.db.execute(
            select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.followee_id == followee_id
                )
            )
        )
        if existing_follow.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已经关注该用户"
            )
        
        # 创建关注关系
        follow = Follow(
            id=str(uuid.uuid4()),
            follower_id=follower_id,
            followee_id=followee_id
        )
        
        self.db.add(follow)
        await self.db.commit()
        await self.db.refresh(follow)
        
        return follow
    
    async def unfollow_user(self, follower_id: str, followee_id: str) -> bool:
        """
        取消关注用户
        
        Args:
            follower_id: 关注者ID
            followee_id: 被关注者ID
            
        Returns:
            是否成功取消关注
            
        Raises:
            HTTPException: 未关注该用户时抛出
        """
        # 查找关注关系
        result = await self.db.execute(
            select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.followee_id == followee_id
                )
            )
        )
        follow = result.scalar_one_or_none()
        
        if not follow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未关注该用户"
            )
        
        # 删除关注关系
        await self.db.delete(follow)
        await self.db.commit()
        
        return True
    
    async def get_following_list(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        获取用户的关注列表
        
        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            关注的用户列表
        """
        # 查询关注关系
        result = await self.db.execute(
            select(User)
            .join(Follow, Follow.followee_id == User.id)
            .where(Follow.follower_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_followers_list(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        获取用户的粉丝列表
        
        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            粉丝用户列表
        """
        # 查询关注关系
        result = await self.db.execute(
            select(User)
            .join(Follow, Follow.follower_id == User.id)
            .where(Follow.followee_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_following_feed(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Content]:
        """
        获取关注用户的内容信息流
        
        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            关注用户发布的内容列表，按发布时间倒序
        """
        from sqlalchemy.orm import selectinload
        
        # 查询关注用户发布的内容，预加载creator
        result = await self.db.execute(
            select(Content)
            .options(selectinload(Content.creator))
            .join(Follow, Follow.followee_id == Content.creator_id)
            .where(
                and_(
                    Follow.follower_id == user_id,
                    Content.status == ContentStatus.PUBLISHED
                )
            )
            .order_by(Content.published_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def is_following(self, follower_id: str, followee_id: str) -> bool:
        """
        检查是否已关注某用户
        
        Args:
            follower_id: 关注者ID
            followee_id: 被关注者ID
            
        Returns:
            是否已关注
        """
        result = await self.db.execute(
            select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.followee_id == followee_id
                )
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def get_follow_counts(self, user_id: str) -> dict:
        """
        获取用户的关注数和粉丝数
        
        Args:
            user_id: 用户ID
            
        Returns:
            包含following_count和followers_count的字典
        """
        # 获取关注数
        following_result = await self.db.execute(
            select(func.count(Follow.id)).where(Follow.follower_id == user_id)
        )
        following_count = following_result.scalar() or 0
        
        # 获取粉丝数
        followers_result = await self.db.execute(
            select(func.count(Follow.id)).where(Follow.followee_id == user_id)
        )
        followers_count = followers_result.scalar() or 0
        
        return {
            "following_count": following_count,
            "followers_count": followers_count
        }
    
    # ==================== 收藏功能 ====================
    
    async def favorite_content(self, user_id: str, content_id: str) -> Interaction:
        """
        收藏内容
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            
        Returns:
            互动记录对象
            
        Raises:
            HTTPException: 内容不存在或已收藏时抛出
        """
        # 验证内容存在
        content_result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = content_result.scalar_one_or_none()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="内容不存在"
            )
        
        # 检查是否已收藏
        existing_favorite_result = await self.db.execute(
            select(Interaction).where(
                and_(
                    Interaction.user_id == user_id,
                    Interaction.content_id == content_id,
                    Interaction.type == InteractionType.FAVORITE
                )
            )
        )
        existing_favorite = existing_favorite_result.scalar_one_or_none()
        if existing_favorite:
            # 幂等性：已收藏则直接返回
            return existing_favorite
        
        # 创建收藏记录
        favorite = Interaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            content_id=content_id,
            type=InteractionType.FAVORITE
        )
        
        self.db.add(favorite)
        
        # 更新内容的收藏计数
        content.favorite_count = (content.favorite_count or 0) + 1
        
        await self.db.commit()
        await self.db.refresh(favorite)
        
        return favorite
    
    async def unfavorite_content(self, user_id: str, content_id: str) -> bool:
        """
        取消收藏内容
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            
        Returns:
            是否成功取消收藏
            
        Raises:
            HTTPException: 未收藏该内容时抛出
        """
        # 查找收藏记录
        result = await self.db.execute(
            select(Interaction).where(
                and_(
                    Interaction.user_id == user_id,
                    Interaction.content_id == content_id,
                    Interaction.type == InteractionType.FAVORITE
                )
            )
        )
        favorite = result.scalar_one_or_none()
        
        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未收藏该内容"
            )
        
        # 删除收藏记录
        await self.db.delete(favorite)
        
        # 更新内容的收藏计数
        content_result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = content_result.scalar_one_or_none()
        if content and content.favorite_count > 0:
            content.favorite_count -= 1
        
        await self.db.commit()
        
        return True
    
    async def get_favorite_list(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Content]:
        """
        获取用户的收藏列表
        
        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            收藏的内容列表，按收藏时间倒序
        """
        from sqlalchemy.orm import selectinload
        
        result = await self.db.execute(
            select(Content)
            .options(selectinload(Content.creator))
            .join(Interaction, Interaction.content_id == Content.id)
            .where(
                and_(
                    Interaction.user_id == user_id,
                    Interaction.type == InteractionType.FAVORITE
                )
            )
            .order_by(Interaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    # ==================== 标记功能 ====================
    
    async def bookmark_content(
        self,
        user_id: str,
        content_id: str,
        note: Optional[str] = None
    ) -> Interaction:
        """
        标记内容并添加笔记
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            note: 笔记内容
            
        Returns:
            互动记录对象
            
        Raises:
            HTTPException: 内容不存在时抛出
        """
        # 验证内容存在
        content_result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = content_result.scalar_one_or_none()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="内容不存在"
            )
        
        # 检查是否已标记
        existing_bookmark = await self.db.execute(
            select(Interaction).where(
                and_(
                    Interaction.user_id == user_id,
                    Interaction.content_id == content_id,
                    Interaction.type == InteractionType.BOOKMARK
                )
            )
        )
        existing = existing_bookmark.scalar_one_or_none()
        
        if existing:
            # 如果已标记，更新笔记
            existing.note = note
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        
        # 创建标记记录
        bookmark = Interaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            content_id=content_id,
            type=InteractionType.BOOKMARK,
            note=note
        )
        
        self.db.add(bookmark)
        await self.db.commit()
        await self.db.refresh(bookmark)
        
        return bookmark
    
    async def update_bookmark_note(
        self,
        user_id: str,
        content_id: str,
        note: str
    ) -> Interaction:
        """
        更新标记笔记
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            note: 新的笔记内容
            
        Returns:
            更新后的互动记录对象
            
        Raises:
            HTTPException: 未标记该内容时抛出
        """
        # 查找标记记录
        result = await self.db.execute(
            select(Interaction).where(
                and_(
                    Interaction.user_id == user_id,
                    Interaction.content_id == content_id,
                    Interaction.type == InteractionType.BOOKMARK
                )
            )
        )
        bookmark = result.scalar_one_or_none()
        
        if not bookmark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未标记该内容"
            )
        
        # 更新笔记
        bookmark.note = note
        await self.db.commit()
        await self.db.refresh(bookmark)
        
        return bookmark
    
    async def delete_bookmark(self, user_id: str, content_id: str) -> bool:
        """
        删除标记
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            
        Returns:
            是否成功删除
            
        Raises:
            HTTPException: 未标记该内容时抛出
        """
        # 查找标记记录
        result = await self.db.execute(
            select(Interaction).where(
                and_(
                    Interaction.user_id == user_id,
                    Interaction.content_id == content_id,
                    Interaction.type == InteractionType.BOOKMARK
                )
            )
        )
        bookmark = result.scalar_one_or_none()
        
        if not bookmark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未标记该内容"
            )
        
        # 删除标记记录
        await self.db.delete(bookmark)
        await self.db.commit()
        
        return True
    
    async def get_bookmark_list(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        """
        获取用户的标记列表
        
        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            标记列表，包含内容和笔记，按标记时间倒序
        """
        from sqlalchemy.orm import selectinload
        
        result = await self.db.execute(
            select(Content, Interaction.note, Interaction.created_at)
            .options(selectinload(Content.creator))
            .join(Interaction, Interaction.content_id == Content.id)
            .where(
                and_(
                    Interaction.user_id == user_id,
                    Interaction.type == InteractionType.BOOKMARK
                )
            )
            .order_by(Interaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        bookmarks = []
        for content, note, created_at in result:
            bookmarks.append({
                "content": content,
                "note": note,
                "bookmarked_at": created_at
            })
        
        return bookmarks
    
    # ==================== 点赞功能 ====================
    
    async def like_content(self, user_id: str, content_id: str) -> Interaction:
        """
        点赞内容
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            
        Returns:
            互动记录对象
            
        Raises:
            HTTPException: 内容不存在或已点赞时抛出
        """
        # 验证内容存在
        content_result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = content_result.scalar_one_or_none()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="内容不存在"
            )
        
        # 检查是否已点赞
        existing_like = await self.db.execute(
            select(Interaction).where(
                and_(
                    Interaction.user_id == user_id,
                    Interaction.content_id == content_id,
                    Interaction.type == InteractionType.LIKE
                )
            )
        )
        if existing_like.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已经点赞该内容"
            )
        
        # 创建点赞记录
        like = Interaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            content_id=content_id,
            type=InteractionType.LIKE
        )
        
        self.db.add(like)
        
        # 更新内容的点赞计数
        content.like_count = (content.like_count or 0) + 1
        
        await self.db.commit()
        await self.db.refresh(like)
        
        return like
    
    async def unlike_content(self, user_id: str, content_id: str) -> bool:
        """
        取消点赞内容
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            
        Returns:
            是否成功取消点赞
            
        Raises:
            HTTPException: 未点赞该内容时抛出
        """
        # 查找点赞记录
        result = await self.db.execute(
            select(Interaction).where(
                and_(
                    Interaction.user_id == user_id,
                    Interaction.content_id == content_id,
                    Interaction.type == InteractionType.LIKE
                )
            )
        )
        like = result.scalar_one_or_none()
        
        if not like:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未点赞该内容"
            )
        
        # 删除点赞记录
        await self.db.delete(like)
        
        # 更新内容的点赞计数
        content_result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = content_result.scalar_one_or_none()
        if content and content.like_count > 0:
            content.like_count -= 1
        
        await self.db.commit()
        
        return True
    
    async def get_like_list(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Content]:
        """
        获取用户的点赞列表
        
        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            点赞的内容列表，按点赞时间倒序
        """
        from sqlalchemy.orm import selectinload
        
        result = await self.db.execute(
            select(Content)
            .options(selectinload(Content.creator))
            .join(Interaction, Interaction.content_id == Content.id)
            .where(
                and_(
                    Interaction.user_id == user_id,
                    Interaction.type == InteractionType.LIKE
                )
            )
            .order_by(Interaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    
    # ==================== 用户活动历史 ====================
    
    async def get_watch_history(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        """
        获取用户的观看历史
        
        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            观看历史列表，包含内容和播放进度信息
        """
        from ..models import PlaybackProgress
        from sqlalchemy.orm import selectinload
        
        result = await self.db.execute(
            select(Content, PlaybackProgress)
            .options(selectinload(Content.creator))
            .join(PlaybackProgress, PlaybackProgress.content_id == Content.id)
            .where(PlaybackProgress.user_id == user_id)
            .order_by(PlaybackProgress.last_played_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        history = []
        for content, progress in result.all():
            history.append({
                "content": content,
                "progress_seconds": progress.progress_seconds,
                "duration_seconds": progress.duration_seconds,
                "progress_percentage": progress.progress_percentage,
                "is_completed": bool(progress.is_completed),
                "last_played_at": progress.last_played_at
            })
        
        return history
    
    async def get_download_list(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        """
        获取用户的下载列表
        
        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            下载列表，包含内容和下载信息
        """
        from ..models import Download
        from sqlalchemy.orm import selectinload
        
        result = await self.db.execute(
            select(Content, Download)
            .options(selectinload(Content.creator))
            .join(Download, Download.content_id == Content.id)
            .where(
                and_(
                    Download.user_id == user_id,
                    Download.download_status == "completed"
                )
            )
            .order_by(Download.completed_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        downloads = []
        for content, download in result.all():
            downloads.append({
                "content": content,
                "file_size": download.file_size,
                "quality": download.quality,
                "downloaded_at": download.completed_at,
                "local_path": download.local_path
            })
        
        return downloads

    
    # ==================== 创作者个人资料 ====================
    
    async def get_creator_profile(
        self,
        creator_id: str
    ) -> dict:
        """
        获取创作者个人资料
        
        Args:
            creator_id: 创作者ID
            
        Returns:
            创作者资料信息，包括基本信息、统计数据等
        """
        # 获取创作者基本信息
        creator = await self.get_user_by_id(creator_id)
        
        if not creator:
            raise ValueError("创作者不存在")
        
        # 获取关注数和粉丝数
        follow_counts = await self.get_follow_counts(creator_id)
        
        # 获取发布内容数量
        from ..models import ContentStatus
        
        content_count_result = await self.db.execute(
            select(func.count(Content.id))
            .where(
                and_(
                    Content.creator_id == creator_id,
                    Content.status == ContentStatus.PUBLISHED
                )
            )
        )
        content_count = content_count_result.scalar()
        
        # 获取总观看数（所有内容的观看数之和）
        total_views_result = await self.db.execute(
            select(func.sum(Content.view_count))
            .where(
                and_(
                    Content.creator_id == creator_id,
                    Content.status == ContentStatus.PUBLISHED
                )
            )
        )
        total_views = total_views_result.scalar() or 0
        
        # 获取总点赞数
        total_likes_result = await self.db.execute(
            select(func.sum(Content.like_count))
            .where(
                and_(
                    Content.creator_id == creator_id,
                    Content.status == ContentStatus.PUBLISHED
                )
            )
        )
        total_likes = total_likes_result.scalar() or 0
        
        return {
            "user": creator,
            "following_count": follow_counts["following_count"],
            "followers_count": follow_counts["followers_count"],
            "content_count": content_count,
            "total_views": total_views,
            "total_likes": total_likes
        }
    
    async def get_creator_contents(
        self,
        creator_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Content]:
        """
        获取创作者的发布内容列表
        
        Args:
            creator_id: 创作者ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            创作者的内容列表
        """
        from ..models import ContentStatus
        from sqlalchemy.orm import selectinload
        
        result = await self.db.execute(
            select(Content)
            .options(selectinload(Content.creator))
            .where(
                and_(
                    Content.creator_id == creator_id,
                    Content.status == ContentStatus.PUBLISHED
                )
            )
            .order_by(Content.published_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        return result.scalars().all()

    # ==================== KOL管理 ====================
    
    @staticmethod
    async def grant_kol_status(db: AsyncSession, user_id: str) -> User:
        """
        授予用户KOL状态
        
        需求：48.1 - 实现KOL创建接口
        需求：48.2 - 授予后台内容上传权限
        需求：48.3 - 添加KOL徽章
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            更新后的用户对象
            
        Raises:
            HTTPException: 用户不存在时抛出
        """
        from sqlalchemy import select
        
        result = await db.execute(select(User).filter(User.id == user_id, User.is_deleted == False))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在或已被删除")
        
        if user.is_kol:
            raise HTTPException(status_code=400, detail="用户已经是KOL")
        
        # 授予KOL状态
        user.is_kol = True
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def revoke_kol_status(db: AsyncSession, user_id: str) -> User:
        """
        撤销用户KOL状态
        
        需求：48.4 - 实现KOL撤销接口
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            更新后的用户对象
            
        Raises:
            HTTPException: 用户不存在时抛出
        """
        from sqlalchemy import select
        
        result = await db.execute(select(User).filter(User.id == user_id, User.is_deleted == False))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在或已被删除")
        
        if not user.is_kol:
            raise HTTPException(status_code=400, detail="用户不是KOL")
        
        # 撤销KOL状态
        user.is_kol = False
        await db.commit()
        await db.refresh(user)
        
        return user

    # ==================== 密码管理 ====================
    
    async def change_password(
        self, 
        user_id: str, 
        old_password: str, 
        new_password: str
    ) -> bool:
        """
        修改用户密码
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            是否成功修改
            
        Raises:
            HTTPException: 用户不存在或旧密码错误时抛出
        """
        # 获取用户
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 验证旧密码
        from ..utils.auth import verify_password, get_password_hash
        if not user.password_hash or not verify_password(old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码错误"
            )
        
        # 生成新密码哈希
        new_password_hash = get_password_hash(new_password)
        
        # 更新密码
        user.password_hash = new_password_hash
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return True
