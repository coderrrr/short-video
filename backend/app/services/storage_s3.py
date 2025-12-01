"""
AWS S3 文件存储服务
实现AWS S3的文件上传、下载和管理
用于生产环境
"""
import hashlib
import logging
from typing import BinaryIO, Optional
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

from app.config import settings
from app.services.storage_interface import StorageInterface

logger = logging.getLogger(__name__)


class S3StorageService(StorageInterface):
    """AWS S3 文件存储服务"""
    
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None
    ):
        """
        初始化S3存储服务
        
        Args:
            bucket_name: S3存储桶名称
            region: AWS区域
            access_key: AWS访问密钥
            secret_key: AWS密钥
        """
        self.bucket_name = bucket_name or settings.S3_BUCKET_NAME
        self.region = region or settings.S3_REGION
        
        # 创建S3客户端
        session_kwargs = {"region_name": self.region}
        if access_key and secret_key:
            session_kwargs.update({
                "aws_access_key_id": access_key,
                "aws_secret_access_key": secret_key
            })
        
        self.s3_client = boto3.client('s3', **session_kwargs)
        logger.info(f"S3存储服务已初始化: bucket={self.bucket_name}, region={self.region}")
    
    def _generate_s3_key(self, file_type: str, filename: str, user_id: Optional[str] = None) -> str:
        """
        生成S3对象键
        
        Args:
            file_type: 文件类型 (videos, covers, avatars)
            filename: 原始文件名
            user_id: 用户ID（可选）
        
        Returns:
            S3对象键
        """
        # 获取当前日期用于目录组织
        now = datetime.now()
        date_path = f"{now.year}/{now.month:02d}/{now.day:02d}"
        
        # 生成唯一文件名
        timestamp = now.strftime("%Y%m%d%H%M%S%f")
        file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
        file_ext = filename.split('.')[-1] if '.' in filename else ''
        unique_filename = f"{timestamp}_{file_hash}.{file_ext}" if file_ext else f"{timestamp}_{file_hash}"
        
        # 构建S3键
        if user_id:
            return f"{file_type}/{date_path}/{user_id}/{unique_filename}"
        else:
            return f"{file_type}/{date_path}/{unique_filename}"
    
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        file_type: str = "videos",
        user_id: Optional[str] = None
    ) -> str:
        """
        上传文件到S3
        
        Args:
            file: 文件对象
            filename: 原始文件名
            file_type: 文件类型 (videos, covers, avatars)
            user_id: 用户ID（可选）
        
        Returns:
            S3对象键
        """
        try:
            # 生成S3键
            s3_key = self._generate_s3_key(file_type, filename, user_id)
            
            # 读取文件内容
            if hasattr(file, 'read'):
                content = file.read()
            else:
                content = file
            
            # 上传到S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content,
                ContentType=self._get_content_type(filename)
            )
            
            logger.info(f"文件上传到S3成功: {s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"S3文件上传失败: {e}")
            raise
    
    async def download_file(self, file_path: str) -> bytes:
        """
        从S3下载文件
        
        Args:
            file_path: S3对象键
        
        Returns:
            文件内容（字节）
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            content = response['Body'].read()
            
            logger.info(f"从S3下载文件成功: {file_path}")
            return content
            
        except ClientError as e:
            logger.error(f"S3文件下载失败: {e}")
            raise
    
    async def delete_file(self, file_path: str) -> bool:
        """
        从S3删除文件
        
        Args:
            file_path: S3对象键
        
        Returns:
            删除成功返回True
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            
            logger.info(f"从S3删除文件成功: {file_path}")
            return True
            
        except ClientError as e:
            logger.error(f"S3文件删除失败: {e}")
            raise
    
    async def file_exists(self, file_path: str) -> bool:
        """
        检查S3文件是否存在
        
        Args:
            file_path: S3对象键
        
        Returns:
            文件存在返回True
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return True
        except ClientError:
            return False
    
    async def get_file_size(self, file_path: str) -> int:
        """
        获取S3文件大小
        
        Args:
            file_path: S3对象键
        
        Returns:
            文件大小（字节）
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return response['ContentLength']
            
        except ClientError as e:
            logger.error(f"获取S3文件大小失败: {e}")
            raise
    
    async def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        获取S3文件的预签名URL
        
        Args:
            file_path: S3对象键
            expires_in: URL过期时间（秒），默认1小时
        
        Returns:
            预签名URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_path
                },
                ExpiresIn=expires_in
            )
            return url
            
        except ClientError as e:
            logger.error(f"生成S3预签名URL失败: {e}")
            raise
    
    async def cleanup_temp_files(self, max_age_hours: int = 24):
        """
        清理S3临时文件
        
        Args:
            max_age_hours: 文件最大保留时间（小时）
        """
        try:
            # 列出temp目录下的所有对象
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix='temp/')
            
            now = datetime.now()
            deleted_count = 0
            
            for page in pages:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    # 检查文件年龄
                    last_modified = obj['LastModified'].replace(tzinfo=None)
                    age_hours = (now - last_modified).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        self.s3_client.delete_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        deleted_count += 1
            
            logger.info(f"S3临时文件清理完成，删除 {deleted_count} 个文件")
            
        except ClientError as e:
            logger.error(f"S3临时文件清理失败: {e}")
    
    async def get_storage_stats(self) -> dict:
        """
        获取S3存储统计信息
        
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
                paginator = self.s3_client.get_paginator('list_objects_v2')
                pages = paginator.paginate(Bucket=self.bucket_name, Prefix=f"{category}/")
                
                for page in pages:
                    if 'Contents' not in page:
                        continue
                    
                    for obj in page['Contents']:
                        size = obj['Size']
                        stats[category]["size"] += size
                        stats[category]["count"] += 1
                        stats["total_size"] += size
                        stats["file_count"] += 1
            
            return stats
            
        except ClientError as e:
            logger.error(f"获取S3存储统计失败: {e}")
            return stats
    
    def _get_content_type(self, filename: str) -> str:
        """
        根据文件名获取Content-Type
        
        Args:
            filename: 文件名
        
        Returns:
            Content-Type
        """
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        content_types = {
            'mp4': 'video/mp4',
            'mov': 'video/quicktime',
            'avi': 'video/x-msvideo',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
        }
        
        return content_types.get(ext, 'application/octet-stream')


# 创建全局实例（仅在配置为S3时）
s3_storage = None
if settings.STORAGE_TYPE == "s3":
    s3_storage = S3StorageService()
