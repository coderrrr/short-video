"""
分享服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, Tuple, List
from datetime import datetime
import uuid

from app.models.share import Share
from app.models.content import Content
from app.models.user import User
from app.config import settings


class ShareService:
    """分享服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_share_link(
        self,
        content_id: str,
        user_id: str,
        platform: str = "wechat"
    ) -> Tuple[str, Content]:
        """
        生成分享链接
        
        Args:
            content_id: 内容ID
            user_id: 用户ID
            platform: 分享平台（wechat/link）
            
        Returns:
            (分享链接, 内容对象)
            
        Raises:
            ValueError: 内容不存在或未发布
        """
        # 验证内容是否存在且已发布
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise ValueError("内容不存在")
        
        if content.status != "published":
            raise ValueError("内容未发布，无法分享")
        
        # 生成分享链接
        # 在实际应用中，这里应该生成一个短链接或深度链接
        # 这里简化为直接使用内容ID
        base_url = getattr(settings, 'APP_BASE_URL', 'https://video.company.com')
        share_url = f"{base_url}/content/{content_id}"
        
        # 如果是企业微信分享，可以添加特殊参数
        if platform == "wechat":
            share_url += "?from=wechat"
        
        # 记录分享行为
        share_record = Share(
            id=str(uuid.uuid4()),
            content_id=content_id,
            user_id=user_id,
            platform=platform,
            created_at=datetime.utcnow()
        )
        
        self.db.add(share_record)
        
        # 更新内容的分享计数
        content.share_count = content.share_count + 1
        
        await self.db.commit()
        
        return share_url, content
    
    async def track_share(
        self,
        content_id: str,
        user_id: str,
        platform: str = "link"
    ) -> Share:
        """
        记录分享行为（不生成链接，仅记录）
        
        Args:
            content_id: 内容ID
            user_id: 用户ID
            platform: 分享平台
            
        Returns:
            分享记录对象
            
        Raises:
            ValueError: 内容不存在
        """
        # 验证内容是否存在
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise ValueError("内容不存在")
        
        # 创建分享记录
        share_record = Share(
            id=str(uuid.uuid4()),
            content_id=content_id,
            user_id=user_id,
            platform=platform,
            created_at=datetime.utcnow()
        )
        
        self.db.add(share_record)
        
        # 更新内容的分享计数
        content.share_count = content.share_count + 1
        
        await self.db.commit()
        await self.db.refresh(share_record)
        
        return share_record
    
    async def get_share_count(self, content_id: str) -> int:
        """
        获取内容的分享次数
        
        Args:
            content_id: 内容ID
            
        Returns:
            分享次数
        """
        result = await self.db.execute(
            select(func.count(Share.id)).where(Share.content_id == content_id)
        )
        return result.scalar()
    
    async def get_user_shares(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Share], int]:
        """
        获取用户的分享记录
        
        Args:
            user_id: 用户ID
            page: 页码（从1开始）
            page_size: 每页数量
            
        Returns:
            (分享记录列表, 总数)
        """
        # 查询总数
        count_result = await self.db.execute(
            select(func.count(Share.id)).where(Share.user_id == user_id)
        )
        total = count_result.scalar()
        
        # 查询分享记录列表
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(Share)
            .where(Share.user_id == user_id)
            .order_by(Share.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        shares = result.scalars().all()
        
        return list(shares), total
    
    async def get_content_shares(
        self,
        content_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Share], int]:
        """
        获取内容的分享记录
        
        Args:
            content_id: 内容ID
            page: 页码（从1开始）
            page_size: 每页数量
            
        Returns:
            (分享记录列表, 总数)
        """
        # 查询总数
        count_result = await self.db.execute(
            select(func.count(Share.id)).where(Share.content_id == content_id)
        )
        total = count_result.scalar()
        
        # 查询分享记录列表
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(Share)
            .where(Share.content_id == content_id)
            .order_by(Share.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        shares = result.scalars().all()
        
        return list(shares), total
