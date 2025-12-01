"""
播放服务
处理视频播放、进度跟踪、质量设置等功能
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import Optional
import uuid
from datetime import datetime

from ..models import PlaybackProgress, Content, User, UserPreference, VideoQualityPreference
from ..schemas.playback_schemas import (
    PlaybackProgressUpdate,
    PlaybackProgressResponse,
    VideoQualitySettings,
    VideoQualityResponse,
    VideoStreamResponse,
    NextVideoResponse
)


class PlaybackService:
    """播放服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def update_playback_progress(
        self,
        user_id: str,
        content_id: str,
        progress_data: PlaybackProgressUpdate
    ) -> PlaybackProgressResponse:
        """
        更新播放进度
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            progress_data: 播放进度数据
            
        Returns:
            PlaybackProgressResponse: 更新后的播放进度
        """
        # 查询是否已存在播放进度记录
        stmt = select(PlaybackProgress).where(
            and_(
                PlaybackProgress.user_id == user_id,
                PlaybackProgress.content_id == content_id
            )
        )
        result = await self.db.execute(stmt)
        progress = result.scalar_one_or_none()
        
        # 标记是否为新观看
        is_new_view = progress is None
        
        # 计算进度百分比
        progress_percentage = (progress_data.progress_seconds / progress_data.duration_seconds) * 100
        
        # 判断是否完成（观看超过90%视为完成）
        is_completed = progress_percentage >= 90.0
        
        if progress:
            # 更新现有记录
            progress.progress_seconds = progress_data.progress_seconds
            progress.duration_seconds = progress_data.duration_seconds
            progress.progress_percentage = progress_percentage
            progress.playback_speed = progress_data.playback_speed
            progress.is_completed = 1 if is_completed else 0
            progress.last_played_at = datetime.utcnow()
            progress.updated_at = datetime.utcnow()
        else:
            # 创建新记录
            progress = PlaybackProgress(
                id=str(uuid.uuid4()),
                user_id=user_id,
                content_id=content_id,
                progress_seconds=progress_data.progress_seconds,
                duration_seconds=progress_data.duration_seconds,
                progress_percentage=progress_percentage,
                playback_speed=progress_data.playback_speed,
                is_completed=1 if is_completed else 0,
                last_played_at=datetime.utcnow()
            )
            self.db.add(progress)
        
        await self.db.commit()
        await self.db.refresh(progress)
        
        # 如果是新观看，增加内容的观看计数
        if is_new_view:
            await self._increment_view_count(content_id)
        
        # 如果完成观看，更新用户偏好
        if is_completed:
            await self._update_user_preference_on_completion(user_id, content_id, progress_data.duration_seconds)
        
        return PlaybackProgressResponse(
            id=progress.id,
            user_id=progress.user_id,
            content_id=progress.content_id,
            progress_seconds=progress.progress_seconds,
            duration_seconds=progress.duration_seconds,
            progress_percentage=progress.progress_percentage,
            playback_speed=progress.playback_speed,
            is_completed=bool(progress.is_completed),
            last_played_at=progress.last_played_at,
            created_at=progress.created_at,
            updated_at=progress.updated_at
        )
    
    async def get_playback_progress(
        self,
        user_id: str,
        content_id: str
    ) -> Optional[PlaybackProgressResponse]:
        """
        获取播放进度
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            
        Returns:
            Optional[PlaybackProgressResponse]: 播放进度，如果不存在则返回None
        """
        stmt = select(PlaybackProgress).where(
            and_(
                PlaybackProgress.user_id == user_id,
                PlaybackProgress.content_id == content_id
            )
        )
        result = await self.db.execute(stmt)
        progress = result.scalar_one_or_none()
        
        if not progress:
            return None
        
        return PlaybackProgressResponse(
            id=progress.id,
            user_id=progress.user_id,
            content_id=progress.content_id,
            progress_seconds=progress.progress_seconds,
            duration_seconds=progress.duration_seconds,
            progress_percentage=progress.progress_percentage,
            playback_speed=progress.playback_speed,
            is_completed=bool(progress.is_completed),
            last_played_at=progress.last_played_at,
            created_at=progress.created_at,
            updated_at=progress.updated_at
        )
    
    async def get_video_stream(
        self,
        content_id: str,
        quality: str = "auto"
    ) -> Optional[VideoStreamResponse]:
        """
        获取视频流URL
        
        Args:
            content_id: 内容ID
            quality: 视频质量（auto, hd, sd）
            
        Returns:
            Optional[VideoStreamResponse]: 视频流信息
        """
        # 查询内容
        stmt = select(Content).where(Content.id == content_id)
        result = await self.db.execute(stmt)
        content = result.scalar_one_or_none()
        
        if not content:
            return None
        
        # 根据质量设置返回不同的视频URL
        # 在实际实现中，这里应该返回不同清晰度的视频URL
        # 目前简化处理，返回原始视频URL
        video_url = content.video_url
        
        return VideoStreamResponse(
            video_url=video_url,
            quality=quality,
            content_type="video/mp4",
            duration_seconds=float(content.duration) if content.duration else 0.0
        )
    
    async def get_next_video(
        self,
        user_id: str,
        current_content_id: str
    ) -> Optional[NextVideoResponse]:
        """
        获取下一个推荐视频
        
        Args:
            user_id: 用户ID
            current_content_id: 当前内容ID
            
        Returns:
            Optional[NextVideoResponse]: 下一个视频信息
        """
        # 简化实现：获取最新发布的视频（排除当前视频）
        # 在实际实现中，应该基于推荐算法
        from ..models import ContentStatus
        
        stmt = select(Content).where(
            and_(
                Content.id != current_content_id,
                Content.status == ContentStatus.PUBLISHED
            )
        ).order_by(desc(Content.published_at)).limit(1)
        
        result = await self.db.execute(stmt)
        next_content = result.scalar_one_or_none()
        
        if not next_content:
            return None
        
        # 获取创作者信息
        creator_stmt = select(User).where(User.id == next_content.creator_id)
        creator_result = await self.db.execute(creator_stmt)
        creator = creator_result.scalar_one_or_none()
        
        return NextVideoResponse(
            content_id=next_content.id,
            title=next_content.title,
            video_url=next_content.video_url,
            cover_url=next_content.cover_url,
            duration_seconds=float(next_content.duration) if next_content.duration else 0.0,
            creator_name=creator.name if creator else "未知创作者"
        )
    
    async def set_video_quality(
        self,
        user_id: str,
        quality_settings: VideoQualitySettings
    ) -> VideoQualityResponse:
        """
        设置视频质量偏好
        
        Args:
            user_id: 用户ID
            quality_settings: 质量设置
            
        Returns:
            VideoQualityResponse: 质量设置响应
        """
        # 验证质量设置
        valid_qualities = ["auto", "hd", "sd"]
        if quality_settings.quality not in valid_qualities:
            raise ValueError(f"无效的视频质量设置: {quality_settings.quality}")
        
        # 查询是否已存在质量偏好
        stmt = select(VideoQualityPreference).where(
            VideoQualityPreference.user_id == user_id
        )
        result = await self.db.execute(stmt)
        preference = result.scalar_one_or_none()
        
        if preference:
            # 更新现有偏好
            preference.quality = quality_settings.quality
            preference.updated_at = datetime.utcnow()
        else:
            # 创建新偏好
            preference = VideoQualityPreference(
                id=str(uuid.uuid4()),
                user_id=user_id,
                quality=quality_settings.quality
            )
            self.db.add(preference)
        
        await self.db.commit()
        
        return VideoQualityResponse(
            quality=quality_settings.quality,
            available_qualities=valid_qualities
        )
    
    async def get_video_quality(
        self,
        user_id: str
    ) -> VideoQualityResponse:
        """
        获取用户的视频质量偏好
        
        Args:
            user_id: 用户ID
            
        Returns:
            VideoQualityResponse: 质量设置响应
        """
        # 查询用户质量偏好
        stmt = select(VideoQualityPreference).where(
            VideoQualityPreference.user_id == user_id
        )
        result = await self.db.execute(stmt)
        preference = result.scalar_one_or_none()
        
        quality = preference.quality if preference else "auto"
        
        return VideoQualityResponse(
            quality=quality,
            available_qualities=["auto", "hd", "sd"]
        )
    
    async def _increment_view_count(self, content_id: str):
        """
        增加内容的观看计数
        
        Args:
            content_id: 内容ID
        """
        stmt = select(Content).where(Content.id == content_id)
        result = await self.db.execute(stmt)
        content = result.scalar_one_or_none()
        
        if content:
            content.view_count = (content.view_count or 0) + 1
            await self.db.commit()
    
    async def _update_user_preference_on_completion(
        self,
        user_id: str,
        content_id: str,
        duration_seconds: float
    ):
        """
        完成观看后更新用户偏好
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            duration_seconds: 视频时长
        """
        # 查询用户偏好
        stmt = select(UserPreference).where(UserPreference.user_id == user_id)
        result = await self.db.execute(stmt)
        preference = result.scalar_one_or_none()
        
        if preference:
            # 更新观看统计
            preference.total_watch_count += 1
            preference.total_watch_duration += duration_seconds
            preference.updated_at = datetime.utcnow()
            await self.db.commit()
