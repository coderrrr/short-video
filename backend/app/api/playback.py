"""
播放相关API端点
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..models import get_db
from ..services.playback_service import PlaybackService
from ..schemas.playback_schemas import (
    PlaybackProgressUpdate,
    PlaybackProgressResponse,
    VideoQualitySettings,
    VideoQualityResponse,
    VideoStreamResponse,
    NextVideoResponse
)
from ..utils.auth import get_current_user
from ..models import User

router = APIRouter(prefix="/playback", tags=["播放"])


@router.post("/progress/{content_id}", response_model=PlaybackProgressResponse)
async def update_playback_progress(
    content_id: str,
    progress_data: PlaybackProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新播放进度
    
    - **content_id**: 内容ID
    - **progress_data**: 播放进度数据
    """
    service = PlaybackService(db)
    
    try:
        progress = await service.update_playback_progress(
            user_id=current_user.id,
            content_id=content_id,
            progress_data=progress_data
        )
        return progress
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新播放进度失败: {str(e)}"
        )


@router.get("/progress/{content_id}", response_model=Optional[PlaybackProgressResponse])
async def get_playback_progress(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取播放进度
    
    - **content_id**: 内容ID
    """
    service = PlaybackService(db)
    
    progress = await service.get_playback_progress(
        user_id=current_user.id,
        content_id=content_id
    )
    
    return progress


@router.get("/stream/{content_id}", response_model=VideoStreamResponse)
async def get_video_stream(
    content_id: str,
    quality: str = "auto",
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频流URL
    
    - **content_id**: 内容ID
    - **quality**: 视频质量（auto, hd, sd）
    """
    service = PlaybackService(db)
    
    stream = await service.get_video_stream(
        content_id=content_id,
        quality=quality
    )
    
    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在"
        )
    
    return stream


@router.get("/next/{content_id}", response_model=Optional[NextVideoResponse])
async def get_next_video(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取下一个推荐视频
    
    - **content_id**: 当前内容ID
    """
    service = PlaybackService(db)
    
    next_video = await service.get_next_video(
        user_id=current_user.id,
        current_content_id=content_id
    )
    
    return next_video


@router.get("/quality", response_model=VideoQualityResponse)
async def get_video_quality(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频质量偏好
    """
    service = PlaybackService(db)
    
    try:
        response = await service.get_video_quality(user_id=current_user.id)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取视频质量失败: {str(e)}"
        )


@router.post("/quality", response_model=VideoQualityResponse)
async def set_video_quality(
    quality_settings: VideoQualitySettings,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    设置视频质量偏好
    
    - **quality_settings**: 质量设置
    """
    service = PlaybackService(db)
    
    try:
        response = await service.set_video_quality(
            user_id=current_user.id,
            quality_settings=quality_settings
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置视频质量失败: {str(e)}"
        )
