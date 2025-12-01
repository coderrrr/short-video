"""
本地文件存储服务
实现本地文件系统的文件上传、下载和管理
"""
import os
import shutil
import hashlib
import logging
from pathlib import Path
from typing import BinaryIO, Optional
from datetime import datetime
import aiofiles
import aiofiles.os

from app.config import settings
from app.services.storage_interface import StorageInterface

logger = logging.getLogger(__name__)


class LocalStorageService(StorageInterface):
    """本地文件存储服务"""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        初始化本地存储服务
        
        Args:
            base_path: 存储根目录，默认使用配置中的路径
        """
        self.base_path = Path(base_path or settings.LOCAL_STORAGE_PATH)
        self._ensure_directory_structure()
    
    def _ensure_directory_structure(self):
        """确保目录结构存在"""
        # 创建主要目录
        directories = [
            self.base_path / "videos",      # 视频文件
            self.base_path / "covers",      # 封面图片
            self.base_path / "avatars",     # 用户头像
            self.base_path / "temp",        # 临时文件
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"本地存储目录结构已创建: {self.base_path}")
    
    def _generate_file_path(self, file_type: str, filename: str, user_id: Optional[str] = None) -> Path:
        """
        生成文件存储路径
        使用日期和用户ID组织文件，避免单个目录文件过多
        
        Args:
            file_type: 文件类型 (videos, covers, avatars)
            filename: 原始文件名
            user_id: 用户ID（可选）
        
        Returns:
            完整的文件路径
        """
        # 获取当前日期用于目录组织
        now = datetime.now()
        date_path = f"{now.year}/{now.month:02d}/{now.day:02d}"
        
        # 生成唯一文件名（使用时间戳和原始文件名的哈希）
        timestamp = now.strftime("%Y%m%d%H%M%S%f")
        file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
        file_ext = Path(filename).suffix
        unique_filename = f"{timestamp}_{file_hash}{file_ext}"
        
        # 构建完整路径
        if user_id:
            return self.base_path / file_type / date_path / user_id / unique_filename
        else:
            return self.base_path / file_type / date_path / unique_filename
    
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        file_type: str = "videos",
        user_id: Optional[str] = None
    ) -> str:
        """
        上传文件到本地存储
        
        Args:
            file: 文件对象
            filename: 原始文件名
            file_type: 文件类型 (videos, covers, avatars)
            user_id: 用户ID（可选）
        
        Returns:
            文件的相对路径
        """
        try:
            # 生成文件路径
            file_path = self._generate_file_path(file_type, filename, user_id)
            
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 异步写入文件
            async with aiofiles.open(file_path, 'wb') as f:
                # 如果file是字节流，直接写入
                if hasattr(file, 'read'):
                    content = file.read()
                    await f.write(content)
                else:
                    await f.write(file)
            
            # 返回相对路径
            relative_path = str(file_path.relative_to(self.base_path))
            logger.info(f"文件上传成功: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            raise
    
    async def download_file(self, file_path: str) -> bytes:
        """
        从本地存储下载文件
        
        Args:
            file_path: 文件的相对路径
        
        Returns:
            文件内容（字节）
        """
        try:
            full_path = self.base_path / file_path
            
            if not full_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            async with aiofiles.open(full_path, 'rb') as f:
                content = await f.read()
            
            logger.info(f"文件下载成功: {file_path}")
            return content
            
        except Exception as e:
            logger.error(f"文件下载失败: {e}")
            raise
    
    async def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件的相对路径
        
        Returns:
            删除成功返回True
        """
        try:
            full_path = self.base_path / file_path
            
            if full_path.exists():
                await aiofiles.os.remove(full_path)
                logger.info(f"文件删除成功: {file_path}")
                return True
            else:
                logger.warning(f"文件不存在，无法删除: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            raise
    
    async def file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件的相对路径
        
        Returns:
            文件存在返回True
        """
        full_path = self.base_path / file_path
        return full_path.exists()
    
    async def get_file_size(self, file_path: str) -> int:
        """
        获取文件大小
        
        Args:
            file_path: 文件的相对路径
        
        Returns:
            文件大小（字节）
        """
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        stat = await aiofiles.os.stat(full_path)
        return stat.st_size
    
    async def get_file_url(self, file_path: str) -> str:
        """
        获取文件访问URL
        本地存储返回相对路径，需要通过API服务访问
        
        Args:
            file_path: 文件的相对路径
        
        Returns:
            文件访问URL
        """
        # 本地存储返回API路径
        return f"/files/{file_path}"
    
    async def cleanup_temp_files(self, max_age_hours: int = 24):
        """
        清理临时文件
        删除超过指定时间的临时文件
        
        Args:
            max_age_hours: 文件最大保留时间（小时）
        """
        temp_dir = self.base_path / "temp"
        if not temp_dir.exists():
            return
        
        now = datetime.now()
        deleted_count = 0
        
        try:
            for file_path in temp_dir.rglob("*"):
                if file_path.is_file():
                    # 获取文件修改时间
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    age_hours = (now - mtime).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        await aiofiles.os.remove(file_path)
                        deleted_count += 1
            
            logger.info(f"临时文件清理完成，删除 {deleted_count} 个文件")
            
        except Exception as e:
            logger.error(f"临时文件清理失败: {e}")
    
    async def get_storage_stats(self) -> dict:
        """
        获取存储统计信息
        
        Returns:
            存储统计信息字典
        """
        stats = {
            "total_size": 0,
            "file_count": 0,
            "videos": {"size": 0, "count": 0},
            "covers": {"size": 0, "count": 0},
            "avatars": {"size": 0, "count": 0},
        }
        
        try:
            for category in ["videos", "covers", "avatars"]:
                category_path = self.base_path / category
                if category_path.exists():
                    for file_path in category_path.rglob("*"):
                        if file_path.is_file():
                            size = file_path.stat().st_size
                            stats[category]["size"] += size
                            stats[category]["count"] += 1
                            stats["total_size"] += size
                            stats["file_count"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"获取存储统计失败: {e}")
            return stats


# 创建全局实例
local_storage = LocalStorageService()
