"""
存储服务接口定义
定义统一的存储接口，支持本地文件系统和AWS S3
"""
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional


class StorageInterface(ABC):
    """存储服务抽象接口"""
    
    @abstractmethod
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        file_type: str = "videos",
        user_id: Optional[str] = None
    ) -> str:
        """
        上传文件
        
        Args:
            file: 文件对象
            filename: 原始文件名
            file_type: 文件类型 (videos, covers, avatars)
            user_id: 用户ID（可选）
        
        Returns:
            文件的存储路径或URL
        """
        pass
    
    @abstractmethod
    async def download_file(self, file_path: str) -> bytes:
        """
        下载文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件内容（字节）
        """
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            删除成功返回True
        """
        pass
    
    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件存在返回True
        """
        pass
    
    @abstractmethod
    async def get_file_size(self, file_path: str) -> int:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件大小（字节）
        """
        pass
    
    @abstractmethod
    async def get_file_url(self, file_path: str) -> str:
        """
        获取文件访问URL
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件访问URL
        """
        pass
    
    @abstractmethod
    async def cleanup_temp_files(self, max_age_hours: int = 24):
        """
        清理临时文件
        
        Args:
            max_age_hours: 文件最大保留时间（小时）
        """
        pass
    
    @abstractmethod
    async def get_storage_stats(self) -> dict:
        """
        获取存储统计信息
        
        Returns:
            存储统计信息字典
        """
        pass
