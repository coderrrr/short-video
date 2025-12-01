"""
播放相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PlaybackProgressUpdate(BaseModel):
    """更新播放进度请求"""
    progress_seconds: float = Field(..., ge=0, description="播放进度（秒）")
    duration_seconds: float = Field(..., gt=0, description="视频总时长（秒）")
    playback_speed: float = Field(default=1.0, ge=0.5, le=2.0, description="播放速度")
    
    class Config:
        json_schema_extra = {
            "example": {
                "progress_seconds": 120.5,
                "duration_seconds": 300.0,
                "playback_speed": 1.5
            }
        }


class PlaybackProgressResponse(BaseModel):
    """播放进度响应"""
    id: str
    user_id: str
    content_id: str
    progress_seconds: float
    duration_seconds: float
    progress_percentage: float
    playback_speed: float
    is_completed: bool
    last_played_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user123",
                "content_id": "content456",
                "progress_seconds": 120.5,
                "duration_seconds": 300.0,
                "progress_percentage": 40.17,
                "playback_speed": 1.5,
                "is_completed": False,
                "last_played_at": "2025-01-15T10:30:00",
                "created_at": "2025-01-15T10:00:00",
                "updated_at": "2025-01-15T10:30:00"
            }
        }


class VideoQualitySettings(BaseModel):
    """视频质量设置"""
    quality: str = Field(..., description="视频质量：auto, hd, sd")
    
    class Config:
        json_schema_extra = {
            "example": {
                "quality": "auto"
            }
        }


class VideoQualityResponse(BaseModel):
    """视频质量响应"""
    quality: str
    available_qualities: list[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "quality": "hd",
                "available_qualities": ["auto", "hd", "sd"]
            }
        }


class VideoStreamResponse(BaseModel):
    """视频流响应"""
    video_url: str
    quality: str
    content_type: str
    duration_seconds: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_url": "https://example.com/videos/video123.mp4",
                "quality": "hd",
                "content_type": "video/mp4",
                "duration_seconds": 300.0
            }
        }


class NextVideoResponse(BaseModel):
    """下一个视频响应"""
    content_id: str
    title: str
    video_url: str
    cover_url: Optional[str]
    duration_seconds: float
    creator_name: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "content_id": "content789",
                "title": "下一个视频标题",
                "video_url": "https://example.com/videos/video789.mp4",
                "cover_url": "https://example.com/covers/cover789.jpg",
                "duration_seconds": 240.0,
                "creator_name": "创作者名称"
            }
        }
