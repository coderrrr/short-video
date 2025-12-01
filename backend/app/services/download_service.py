"""
下载服务
处理视频下载、进度跟踪、存储管理等功能
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from typing import Optional, List
import uuid
import os
from datetime import datetime

from ..models import Download, Content, User
from ..schemas.download_schemas import (
    DownloadRequest,
    DownloadResponse,
    DownloadListResponse,
    StorageInfoResponse
)


class DownloadService:
    """下载服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_download(
        self,
        user_id: str,
        content_id: str,
        download_request: DownloadRequest
    ) -> DownloadResponse:
        """
        创建下载任务
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            download_request: 下载请求
            
        Returns:
            DownloadResponse: 下载任务信息
        """
        # 查询内容
        stmt = select(Content).where(Content.id == content_id)
        result = await self.db.execute(stmt)
        content = result.scalar_one_or_none()
        
        if not content:
            raise ValueError("内容不存在")
        
        # 检查是否已存在下载记录
        existing_stmt = select(Download).where(
            and_(
                Download.user_id == user_id,
                Download.content_id == content_id,
                Download.download_status.in_(["pending", "downloading", "completed"])
            )
        )
        existing_result = await self.db.execute(existing_stmt)
        existing_download = existing_result.scalar_one_or_none()
        
        if existing_download:
            # 如果已存在，返回现有记录
            return self._to_response(existing_download)
        
        # 创建新的下载记录
        download = Download(
            id=str(uuid.uuid4()),
            user_id=user_id,
            content_id=content_id,
            file_size=float(content.file_size) if content.file_size else 0.0,
            download_progress=0.0,
            download_status="pending",
            quality=download_request.quality
        )
        
        self.db.add(download)
        await self.db.commit()
        await self.db.refresh(download)
        
        return self._to_response(download)
    
    async def update_download_progress(
        self,
        download_id: str,
        progress: float,
        status: str = "downloading"
    ) -> DownloadResponse:
        """
        更新下载进度
        
        Args:
            download_id: 下载ID
            progress: 下载进度（0-100）
            status: 下载状态
            
        Returns:
            DownloadResponse: 更新后的下载信息
        """
        stmt = select(Download).where(Download.id == download_id)
        result = await self.db.execute(stmt)
        download = result.scalar_one_or_none()
        
        if not download:
            raise ValueError("下载记录不存在")
        
        download.download_progress = progress
        download.download_status = status
        download.updated_at = datetime.utcnow()
        
        if status == "completed":
            download.completed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(download)
        
        return self._to_response(download)
    
    async def get_user_downloads(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> DownloadListResponse:
        """
        获取用户的下载列表
        
        Args:
            user_id: 用户ID
            status: 下载状态过滤（可选）
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            DownloadListResponse: 下载列表
        """
        # 构建查询
        conditions = [Download.user_id == user_id]
        if status:
            conditions.append(Download.download_status == status)
        
        stmt = select(Download).where(
            and_(*conditions)
        ).order_by(desc(Download.created_at)).limit(limit).offset(offset)
        
        result = await self.db.execute(stmt)
        downloads = result.scalars().all()
        
        # 获取总数
        count_stmt = select(func.count(Download.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()
        
        return DownloadListResponse(
            downloads=[self._to_response(d) for d in downloads],
            total=total
        )
    
    async def delete_download(
        self,
        user_id: str,
        download_id: str
    ) -> bool:
        """
        删除下载记录
        
        Args:
            user_id: 用户ID
            download_id: 下载ID
            
        Returns:
            bool: 是否删除成功
        """
        stmt = select(Download).where(
            and_(
                Download.id == download_id,
                Download.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        download = result.scalar_one_or_none()
        
        if not download:
            return False
        
        # 如果有本地文件，删除文件
        if download.local_path and os.path.exists(download.local_path):
            try:
                os.remove(download.local_path)
            except Exception as e:
                print(f"删除本地文件失败: {e}")
        
        await self.db.delete(download)
        await self.db.commit()
        
        return True
    
    async def get_storage_info(
        self,
        user_id: str
    ) -> StorageInfoResponse:
        """
        获取存储空间信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            StorageInfoResponse: 存储空间信息
        """
        # 查询用户的所有已完成下载
        stmt = select(Download).where(
            and_(
                Download.user_id == user_id,
                Download.download_status == "completed"
            )
        )
        result = await self.db.execute(stmt)
        downloads = result.scalars().all()
        
        # 计算已使用空间
        used_space = sum(d.file_size for d in downloads)
        
        # 模拟总空间和可用空间（实际应该从系统获取）
        total_space = 10 * 1024 * 1024 * 1024  # 10GB
        available_space = total_space - used_space
        
        return StorageInfoResponse(
            total_space=total_space,
            used_space=used_space,
            available_space=available_space,
            download_count=len(downloads)
        )
    
    async def clear_user_downloads(self, user_id: str) -> int:
        """
        清除用户的所有下载记录
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 清除的下载记录数量
        """
        # 查询用户的所有下载
        stmt = select(Download).where(Download.user_id == user_id)
        result = await self.db.execute(stmt)
        downloads = result.scalars().all()
        
        count = 0
        for download in downloads:
            # 如果有本地文件，删除文件
            if download.local_path and os.path.exists(download.local_path):
                try:
                    os.remove(download.local_path)
                except Exception as e:
                    print(f"删除本地文件失败: {e}")
            
            await self.db.delete(download)
            count += 1
        
        await self.db.commit()
        return count
    
    def _to_response(self, download: Download) -> DownloadResponse:
        """将Download模型转换为响应对象"""
        return DownloadResponse(
            id=download.id,
            user_id=download.user_id,
            content_id=download.content_id,
            file_size=download.file_size,
            download_progress=download.download_progress,
            download_status=download.download_status,
            local_path=download.local_path,
            quality=download.quality,
            created_at=download.created_at,
            updated_at=download.updated_at,
            completed_at=download.completed_at
        )
