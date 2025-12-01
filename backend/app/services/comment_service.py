"""
评论服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from datetime import datetime
import uuid

from app.models.comment import Comment
from app.models.content import Content
from app.models.user import User
from app.schemas.comment_schemas import CommentCreate, CommentUpdate


class CommentService:
    """评论服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_comment(
        self,
        user_id: str,
        comment_data: CommentCreate
    ) -> Comment:
        """
        创建评论
        
        Args:
            user_id: 用户ID
            comment_data: 评论数据
            
        Returns:
            创建的评论对象
            
        Raises:
            ValueError: 内容不存在或父评论不存在
        """
        # 验证内容是否存在
        content_result = await self.db.execute(
            select(Content).where(Content.id == comment_data.content_id)
        )
        content = content_result.scalar_one_or_none()
        
        if not content:
            raise ValueError("内容不存在")
        
        # 如果是回复评论，验证父评论是否存在
        if comment_data.parent_id:
            parent_result = await self.db.execute(
                select(Comment).where(Comment.id == comment_data.parent_id)
            )
            parent_comment = parent_result.scalar_one_or_none()
            
            if not parent_comment:
                raise ValueError("父评论不存在")
            
            # 验证父评论属于同一内容
            if parent_comment.content_id != comment_data.content_id:
                raise ValueError("父评论不属于该内容")
        
        # 验证提及的用户是否存在
        if comment_data.mentioned_users:
            for mentioned_user_id in comment_data.mentioned_users:
                user_result = await self.db.execute(
                    select(User).where(User.id == mentioned_user_id)
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    raise ValueError(f"提及的用户不存在: {mentioned_user_id}")
        
        # 创建评论
        comment = Comment(
            id=str(uuid.uuid4()),
            content_id=comment_data.content_id,
            user_id=user_id,
            text=comment_data.text,
            parent_id=comment_data.parent_id,
            mentioned_users=comment_data.mentioned_users or [],
            created_at=datetime.utcnow()
        )
        
        self.db.add(comment)
        
        # 更新内容的评论计数
        content.comment_count = content.comment_count + 1
        
        await self.db.commit()
        await self.db.refresh(comment)
        
        # TODO: 发送通知给被@提及的用户
        # TODO: 如果是回复评论，通知原评论作者
        
        return comment
    
    async def get_comment(self, comment_id: str) -> Optional[Comment]:
        """
        获取评论详情
        
        Args:
            comment_id: 评论ID
            
        Returns:
            评论对象，如果不存在则返回None
        """
        result = await self.db.execute(
            select(Comment)
            .options(selectinload(Comment.user))
            .where(Comment.id == comment_id)
        )
        return result.scalar_one_or_none()
    
    async def list_comments(
        self,
        content_id: str,
        page: int = 1,
        page_size: int = 20,
        parent_id: Optional[str] = None
    ) -> Tuple[List[Comment], int]:
        """
        查询评论列表
        
        Args:
            content_id: 内容ID
            page: 页码（从1开始）
            page_size: 每页数量
            parent_id: 父评论ID（如果为None，则查询顶级评论；如果指定，则查询回复）
            
        Returns:
            (评论列表, 总数)
        """
        # 构建查询条件
        conditions = [Comment.content_id == content_id]
        
        if parent_id is None:
            # 查询顶级评论（没有父评论）
            conditions.append(Comment.parent_id.is_(None))
        else:
            # 查询特定评论的回复
            conditions.append(Comment.parent_id == parent_id)
        
        # 查询总数
        count_result = await self.db.execute(
            select(func.count(Comment.id)).where(and_(*conditions))
        )
        total = count_result.scalar()
        
        # 查询评论列表
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(Comment)
            .options(selectinload(Comment.user))
            .where(and_(*conditions))
            .order_by(Comment.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        comments = result.scalars().all()
        
        return list(comments), total
    
    async def get_reply_count(self, comment_id: str) -> int:
        """
        获取评论的回复数量
        
        Args:
            comment_id: 评论ID
            
        Returns:
            回复数量
        """
        result = await self.db.execute(
            select(func.count(Comment.id)).where(Comment.parent_id == comment_id)
        )
        return result.scalar()
    
    async def update_comment(
        self,
        comment_id: str,
        user_id: str,
        comment_data: CommentUpdate
    ) -> Comment:
        """
        更新评论
        
        Args:
            comment_id: 评论ID
            user_id: 用户ID
            comment_data: 更新的评论数据
            
        Returns:
            更新后的评论对象
            
        Raises:
            ValueError: 评论不存在或无权限
        """
        # 获取评论
        comment = await self.get_comment(comment_id)
        
        if not comment:
            raise ValueError("评论不存在")
        
        # 验证权限（只有评论作者可以编辑）
        if comment.user_id != user_id:
            raise ValueError("无权限编辑此评论")
        
        # 更新评论
        comment.text = comment_data.text
        
        await self.db.commit()
        await self.db.refresh(comment)
        
        return comment
    
    async def delete_comment(
        self,
        comment_id: str,
        user_id: str,
        is_admin: bool = False
    ) -> bool:
        """
        删除评论
        
        Args:
            comment_id: 评论ID
            user_id: 用户ID
            is_admin: 是否为管理员
            
        Returns:
            是否删除成功
            
        Raises:
            ValueError: 评论不存在或无权限
        """
        # 获取评论
        comment = await self.get_comment(comment_id)
        
        if not comment:
            raise ValueError("评论不存在")
        
        # 验证权限（评论作者或管理员可以删除）
        if comment.user_id != user_id and not is_admin:
            raise ValueError("无权限删除此评论")
        
        # 获取内容
        content_result = await self.db.execute(
            select(Content).where(Content.id == comment.content_id)
        )
        content = content_result.scalar_one_or_none()
        
        # 删除评论（级联删除回复）
        await self.db.delete(comment)
        
        # 更新内容的评论计数
        if content:
            # 计算要减少的评论数（包括回复）
            reply_count = await self.get_reply_count(comment_id)
            content.comment_count = max(0, content.comment_count - 1 - reply_count)
        
        await self.db.commit()
        
        return True
    
    async def get_user_comments(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Comment], int]:
        """
        获取用户的评论列表
        
        Args:
            user_id: 用户ID
            page: 页码（从1开始）
            page_size: 每页数量
            
        Returns:
            (评论列表, 总数)
        """
        # 查询总数
        count_result = await self.db.execute(
            select(func.count(Comment.id)).where(Comment.user_id == user_id)
        )
        total = count_result.scalar()
        
        # 查询评论列表
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(Comment)
            .options(selectinload(Comment.user))
            .options(selectinload(Comment.content))
            .where(Comment.user_id == user_id)
            .order_by(Comment.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        comments = result.scalars().all()
        
        return list(comments), total
