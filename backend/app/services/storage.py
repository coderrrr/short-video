"""
存储服务工厂
根据配置自动选择本地存储或S3存储
"""
import logging
from typing import Optional

from app.config import settings
from app.services.storage_interface import StorageInterface
from app.services.storage_local import LocalStorageService
from app.services.storage_s3 import S3StorageService

logger = logging.getLogger(__name__)


class StorageFactory:
    """存储服务工厂"""
    
    _instance: Optional[StorageInterface] = None
    
    @classmethod
    def get_storage(cls) -> StorageInterface:
        """
        获取存储服务实例
        根据配置返回本地存储或S3存储
        使用单例模式确保全局只有一个实例
        
        Returns:
            存储服务实例
        """
        if cls._instance is None:
            storage_type = settings.STORAGE_TYPE.lower()
            
            if storage_type == "local":
                logger.info("使用本地文件存储")
                cls._instance = LocalStorageService()
            elif storage_type == "s3":
                logger.info("使用AWS S3存储")
                cls._instance = S3StorageService()
            else:
                logger.warning(f"未知的存储类型: {storage_type}，使用本地存储")
                cls._instance = LocalStorageService()
        
        return cls._instance
    
    @classmethod
    def reset(cls):
        """重置存储服务实例（主要用于测试）"""
        cls._instance = None


# 便捷函数：获取存储服务
def get_storage() -> StorageInterface:
    """
    获取存储服务实例
    
    使用示例:
        from app.services.storage import get_storage
        
        storage = get_storage()
        file_path = await storage.upload_file(file, "video.mp4", "videos", user_id)
    
    Returns:
        存储服务实例
    """
    return StorageFactory.get_storage()
