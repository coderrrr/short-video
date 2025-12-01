"""
下载相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DownloadRequest(BaseModel):
    """下载请求"""
    quality: str = Field(default="hd", description="下载质量：hd, sd")
    
    class Config:
        json_schema_extra = {
            "example": {
                "quality": "hd"
            }
        }


class DownloadResponse(BaseModel):
    """下载响应"""
    id: str
    user_id: str
    content_id: str
    file_size: float
    download_progress: float
    download_status: str
    local_path: Optional[str]
    quality: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user123",
                "content_id": "content456",
                "file_size": 104857600.0,
                "download_progress": 75.5,
                "download_status": "downloading",
                "local_path": "/storage/downloads/video123.mp4",
                "quality": "hd",
                "created_at": "2025-01-15T10:00:00",
                "updated_at": "2025-01-15T10:05:00",
                "completed_at": None
            }
        }


class DownloadListResponse(BaseModel):
    """下载列表响应"""
    downloads: list[DownloadResponse]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "downloads": [],
                "total": 0
            }
        }


class StorageInfoResponse(BaseModel):
    """存储空间信息响应"""
    total_space: float
    used_space: float
    available_space: float
    download_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_space": 10737418240.0,
                "used_space": 2147483648.0,
                "available_space": 8589934592.0,
                "download_count": 5
            }
        }
