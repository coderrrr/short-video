"""
内容服务 - 处理视频上传、元数据管理等
"""
import uuid
import os
import subprocess
from typing import Optional, List, BinaryIO
from datetime import datetime, timedelta
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.content import Content, ContentStatus
from app.models.content_tag import ContentTag
from app.models.review_record import ReviewRecord
from app.models.user import User
from app.services.storage import get_storage
from app.schemas.content_schemas import VideoMetadataCreate, VideoMetadataUpdate
import logging

logger = logging.getLogger(__name__)


class ContentService:
    """内容服务类"""
    
    # 支持的视频格式
    SUPPORTED_VIDEO_FORMATS = ['mp4', 'mov', 'avi']
    
    # 支持的图片格式
    SUPPORTED_IMAGE_FORMATS = ['jpg', 'jpeg', 'png']
    
    # 最大文件大小（字节）- 默认500MB
    MAX_VIDEO_SIZE = 500 * 1024 * 1024
    
    # 压缩阈值（字节）- 50MB
    COMPRESSION_THRESHOLD = 50 * 1024 * 1024
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = get_storage()
    
    def _validate_video_format(self, filename: str) -> bool:
        """
        验证视频格式
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 格式是否支持
        """
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        return ext in self.SUPPORTED_VIDEO_FORMATS
    
    def _validate_image_format(self, filename: str) -> bool:
        """
        验证图片格式
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 格式是否支持
        """
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        return ext in self.SUPPORTED_IMAGE_FORMATS
    
    def _validate_file_size(self, file_size: int) -> bool:
        """
        验证文件大小
        
        Args:
            file_size: 文件大小（字节）
            
        Returns:
            bool: 大小是否符合要求
        """
        return file_size <= self.MAX_VIDEO_SIZE
    
    async def _get_video_duration(self, file_path: str) -> Optional[int]:
        """
        获取视频时长（秒）
        
        Args:
            file_path: 视频文件路径
            
        Returns:
            Optional[int]: 视频时长（秒），失败返回None
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                return int(duration)
        except Exception as e:
            logger.error(f"获取视频时长失败: {e}")
        return None
    
    async def upload_video(
        self,
        file: UploadFile,
        user_id: str,
        metadata: VideoMetadataCreate
    ) -> Content:
        """
        上传视频
        
        Args:
            file: 上传的文件
            user_id: 用户ID
            metadata: 视频元数据
            
        Returns:
            Content: 创建的内容对象
            
        Raises:
            HTTPException: 验证失败或上传失败
        """
        # 1. 验证视频格式
        if not self._validate_video_format(file.filename):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "VIDEO_FORMAT_UNSUPPORTED",
                    "message": f"不支持的视频格式，请上传{', '.join(self.SUPPORTED_VIDEO_FORMATS).upper()}格式的视频",
                    "details": {
                        "uploaded_format": file.filename.rsplit('.', 1)[-1] if '.' in file.filename else 'unknown',
                        "supported_formats": self.SUPPORTED_VIDEO_FORMATS
                    }
                }
            )
        
        # 2. 读取文件内容并验证大小
        file_content = await file.read()
        file_size = len(file_content)
        
        if not self._validate_file_size(file_size):
            max_size_mb = self.MAX_VIDEO_SIZE / (1024 * 1024)
            actual_size_mb = file_size / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "FILE_SIZE_EXCEEDED",
                    "message": f"文件大小超过限制，最大允许{max_size_mb:.0f}MB",
                    "details": {
                        "max_size_mb": max_size_mb,
                        "actual_size_mb": round(actual_size_mb, 2)
                    }
                }
            )
        
        # 3. 生成唯一的内容ID和文件名
        content_id = str(uuid.uuid4())
        file_ext = file.filename.rsplit('.', 1)[-1].lower()
        object_key = f"videos/{content_id}.{file_ext}"
        
        # 4. 上传到存储服务
        try:
            # 将字节内容转换为文件对象
            from io import BytesIO
            file_obj = BytesIO(file_content)
            
            video_url = await self.storage.upload_file(
                file_obj,
                file.filename,
                file_type="videos",
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"视频上传失败: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "UPLOAD_FAILED",
                    "message": "视频上传失败，请稍后重试",
                    "details": {"error": str(e)}
                }
            )
        
        # 5. 创建内容记录
        content = Content(
            id=content_id,
            title=metadata.title,
            description=metadata.description,
            video_url=video_url,
            file_size=file_size,
            creator_id=user_id,
            status=ContentStatus.DRAFT,
            content_type=metadata.content_type,
            created_at=datetime.utcnow()
        )
        
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)
        
        logger.info(f"视频上传成功: content_id={content_id}, user_id={user_id}")
        
        return content
    
    async def update_metadata(
        self,
        content_id: str,
        user_id: str,
        metadata: VideoMetadataUpdate
    ) -> Content:
        """
        更新视频元数据
        
        Args:
            content_id: 内容ID
            user_id: 用户ID
            metadata: 更新的元数据
            
        Returns:
            Content: 更新后的内容对象
            
        Raises:
            HTTPException: 内容不存在或无权限
        """
        # 查询内容
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "CONTENT_NOT_FOUND",
                    "message": "内容不存在"
                }
            )
        
        # 验证权限
        if content.creator_id != user_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": "无权限修改此内容"
                }
            )
        
        # 验证状态（审核中的内容不可编辑）
        if content.status == ContentStatus.UNDER_REVIEW:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "CONTENT_UNDER_REVIEW",
                    "message": "审核中的内容不可编辑"
                }
            )
        
        # 更新元数据
        if metadata.title is not None:
            content.title = metadata.title
        if metadata.description is not None:
            content.description = metadata.description
        if metadata.content_type is not None:
            content.content_type = metadata.content_type
        if metadata.cover_url is not None:
            content.cover_url = metadata.cover_url
        
        content.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(content)
        
        logger.info(f"元数据更新成功: content_id={content_id}")
        
        return content
    
    async def upload_cover_image(
        self,
        content_id: str,
        user_id: str,
        file: UploadFile
    ) -> str:
        """
        上传封面图片
        
        Args:
            content_id: 内容ID
            user_id: 用户ID
            file: 上传的图片文件
            
        Returns:
            str: 封面图片URL
            
        Raises:
            HTTPException: 验证失败或上传失败
        """
        # 1. 验证图片格式
        if not self._validate_image_format(file.filename):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "IMAGE_FORMAT_UNSUPPORTED",
                    "message": f"不支持的图片格式，请上传{', '.join(self.SUPPORTED_IMAGE_FORMATS).upper()}格式的图片",
                    "details": {
                        "uploaded_format": file.filename.rsplit('.', 1)[-1] if '.' in file.filename else 'unknown',
                        "supported_formats": self.SUPPORTED_IMAGE_FORMATS
                    }
                }
            )
        
        # 2. 查询内容并验证权限
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "CONTENT_NOT_FOUND",
                    "message": "内容不存在"
                }
            )
        
        if content.creator_id != user_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": "无权限修改此内容"
                }
            )
        
        # 3. 读取文件内容
        file_content = await file.read()
        
        # 4. 生成文件名并上传
        try:
            # 将字节内容转换为文件对象
            from io import BytesIO
            file_obj = BytesIO(file_content)
            
            cover_url = await self.storage.upload_file(
                file_obj,
                file.filename,
                file_type="covers",
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"封面图片上传失败: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "UPLOAD_FAILED",
                    "message": "封面图片上传失败，请稍后重试",
                    "details": {"error": str(e)}
                }
            )
        
        # 5. 更新内容记录
        content.cover_url = cover_url
        content.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        logger.info(f"封面图片上传成功: content_id={content_id}")
        
        return cover_url
    
    async def extract_video_frames(
        self,
        content_id: str,
        user_id: str,
        interval: int = 5
    ) -> List[str]:
        """
        提取视频帧
        
        Args:
            content_id: 内容ID
            user_id: 用户ID
            interval: 提取间隔（秒）
            
        Returns:
            List[str]: 视频帧URL列表
            
        Raises:
            HTTPException: 内容不存在或提取失败
        """
        # 查询内容并验证权限
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "CONTENT_NOT_FOUND",
                    "message": "内容不存在"
                }
            )
        
        if content.creator_id != user_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": "无权限访问此内容"
                }
            )
        
        # TODO: 实现视频帧提取逻辑
        # 这需要下载视频、使用FFmpeg提取帧、上传帧图片
        # 暂时返回空列表
        logger.warning(f"视频帧提取功能尚未实现: content_id={content_id}")
        return []
    
    async def get_content(self, content_id: str) -> Optional[Content]:
        """
        获取内容详情
        
        Args:
            content_id: 内容ID
            
        Returns:
            Optional[Content]: 内容对象，不存在返回None
        """
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(Content).options(selectinload(Content.creator)).where(Content.id == content_id)
        )
        return result.scalar_one_or_none()
    
    async def save_draft(
        self,
        content_id: str,
        user_id: str
    ) -> Content:
        """
        保存草稿
        
        Args:
            content_id: 内容ID
            user_id: 用户ID
            
        Returns:
            Content: 保存的草稿对象
            
        Raises:
            HTTPException: 内容不存在或无权限
        """
        # 查询内容
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "CONTENT_NOT_FOUND",
                    "message": "内容不存在"
                }
            )
        
        # 验证权限
        if content.creator_id != user_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": "无权限修改此内容"
                }
            )
        
        # 设置为草稿状态
        content.status = ContentStatus.DRAFT
        content.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(content)
        
        logger.info(f"草稿保存成功: content_id={content_id}")
        
        return content
    
    async def load_draft(
        self,
        content_id: str,
        user_id: str
    ) -> Content:
        """
        加载草稿
        
        Args:
            content_id: 内容ID
            user_id: 用户ID
            
        Returns:
            Content: 草稿对象
            
        Raises:
            HTTPException: 内容不存在、无权限或不是草稿
        """
        # 查询内容
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "CONTENT_NOT_FOUND",
                    "message": "内容不存在"
                }
            )
        
        # 验证权限
        if content.creator_id != user_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": "无权限访问此内容"
                }
            )
        
        # 验证是草稿状态
        if content.status != ContentStatus.DRAFT:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "NOT_A_DRAFT",
                    "message": "该内容不是草稿"
                }
            )
        
        logger.info(f"草稿加载成功: content_id={content_id}")
        
        return content
    
    async def list_drafts(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Content], int]:
        """
        查询用户的草稿列表
        
        Args:
            user_id: 用户ID
            page: 页码（从1开始）
            page_size: 每页数量
            
        Returns:
            tuple[List[Content], int]: (草稿列表, 总数)
        """
        from sqlalchemy import func
        
        # 查询总数
        count_result = await self.db.execute(
            select(func.count(Content.id)).where(
                Content.creator_id == user_id,
                Content.status == ContentStatus.DRAFT
            )
        )
        total = count_result.scalar()
        
        # 查询草稿列表
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(Content)
            .where(
                Content.creator_id == user_id,
                Content.status == ContentStatus.DRAFT
            )
            .order_by(Content.updated_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        drafts = result.scalars().all()
        
        logger.info(f"草稿列表查询成功: user_id={user_id}, count={len(drafts)}")
        
        return list(drafts), total
    
    async def delete_draft(
        self,
        content_id: str,
        user_id: str
    ) -> bool:
        """
        删除草稿
        
        Args:
            content_id: 内容ID
            user_id: 用户ID
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            HTTPException: 内容不存在、无权限或不是草稿
        """
        # 查询内容
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "CONTENT_NOT_FOUND",
                    "message": "内容不存在"
                }
            )
        
        # 验证权限
        if content.creator_id != user_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": "无权限删除此内容"
                }
            )
        
        # 验证是草稿状态
        if content.status != ContentStatus.DRAFT:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "NOT_A_DRAFT",
                    "message": "只能删除草稿状态的内容"
                }
            )
        
        # 删除视频文件
        try:
            if content.video_url:
                await self.storage.delete_file(content.video_url)
        except Exception as e:
            logger.warning(f"删除视频文件失败: {e}")
        
        # 删除封面图片
        try:
            if content.cover_url:
                await self.storage.delete_file(content.cover_url)
        except Exception as e:
            logger.warning(f"删除封面图片失败: {e}")
        
        # 删除数据库记录
        await self.db.delete(content)
        await self.db.commit()
        
        logger.info(f"草稿删除成功: content_id={content_id}")
        
        return True
    
    async def submit_for_review(
        self,
        content_id: str,
        user_id: str
    ) -> Content:
        """
        提交内容进行审核
        
        Args:
            content_id: 内容ID
            user_id: 用户ID
            
        Returns:
            Content: 提交的内容对象
            
        Raises:
            HTTPException: 内容不存在、无权限或状态不正确
        """
        from app.models.review_record import ReviewRecord
        
        # 查询内容
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "CONTENT_NOT_FOUND",
                    "message": "内容不存在"
                }
            )
        
        # 验证权限
        if content.creator_id != user_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": "无权限提交此内容"
                }
            )
        
        # 验证状态（只能从草稿或已驳回状态提交）
        if content.status not in [ContentStatus.DRAFT, ContentStatus.REJECTED]:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_STATUS",
                    "message": f"当前状态（{content.status}）不能提交审核"
                }
            )
        
        # 验证必填字段
        if not content.title or not content.title.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "TITLE_REQUIRED",
                    "message": "标题不能为空"
                }
            )
        
        # 更新状态为审核中
        content.status = ContentStatus.UNDER_REVIEW
        content.updated_at = datetime.utcnow()
        
        # 创建审核记录
        review_record = ReviewRecord(
            id=str(uuid.uuid4()),
            content_id=content_id,
            reviewer_id=user_id,  # 暂时使用创建者ID，实际应该是审核员ID
            review_type="platform_review",
            status="pending",
            created_at=datetime.utcnow()
        )
        
        self.db.add(review_record)
        await self.db.commit()
        await self.db.refresh(content)
        
        logger.info(f"内容提交审核成功: content_id={content_id}")
        
        # TODO: 发送通知给审核员
        
        return content
    
    async def approve_content(
        self,
        content_id: str,
        reviewer_id: str,
        comment: Optional[str] = None,
        review_type: str = "platform_review"
    ) -> Content:
        """
        批准内容
        
        Args:
            content_id: 内容ID
            reviewer_id: 审核员ID
            comment: 审核备注（可选）
            review_type: 审核类型
            
        Returns:
            Content: 批准的内容对象
            
        Raises:
            ValueError: 内容不存在或状态不正确
        """
        from app.models.review_record import ReviewRecord
        
        # 查询内容
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise ValueError("内容不存在")
        
        # 验证状态
        if content.status != ContentStatus.UNDER_REVIEW:
            raise ValueError("只能批准审核中的内容")
        
        # 更新状态为已发布
        content.status = ContentStatus.PUBLISHED
        content.published_at = datetime.utcnow()
        content.updated_at = datetime.utcnow()
        
        # 创建审核记录
        review_record = ReviewRecord(
            id=str(uuid.uuid4()),
            content_id=content_id,
            reviewer_id=reviewer_id,
            review_type=review_type,
            status="approved",
            reason=comment,  # 使用reason字段存储备注
            created_at=datetime.utcnow()
        )
        
        self.db.add(review_record)
        await self.db.commit()
        await self.db.refresh(content)
        
        logger.info(f"内容批准成功: content_id={content_id}, reviewer_id={reviewer_id}")
        
        # TODO: 发送通知给创作者
        
        return content
    
    async def reject_content(
        self,
        content_id: str,
        reviewer_id: str,
        reason: str,
        review_type: str = "platform_review"
    ) -> Content:
        """
        拒绝内容
        
        Args:
            content_id: 内容ID
            reviewer_id: 审核员ID
            reason: 拒绝原因
            review_type: 审核类型
            
        Returns:
            Content: 拒绝的内容对象
            
        Raises:
            ValueError: 内容不存在或状态不正确
        """
        from app.models.review_record import ReviewRecord
        
        # 查询内容
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise ValueError("内容不存在")
        
        # 验证状态
        if content.status != ContentStatus.UNDER_REVIEW:
            raise ValueError("只能拒绝审核中的内容")
        
        # 验证拒绝原因
        if not reason or not reason.strip():
            raise ValueError("拒绝原因不能为空")
        
        # 更新状态为已驳回
        content.status = ContentStatus.REJECTED
        content.updated_at = datetime.utcnow()
        
        # 创建审核记录
        review_record = ReviewRecord(
            id=str(uuid.uuid4()),
            content_id=content_id,
            reviewer_id=reviewer_id,
            review_type=review_type,
            status="rejected",
            reason=reason,
            created_at=datetime.utcnow()
        )
        
        self.db.add(review_record)
        await self.db.commit()
        await self.db.refresh(content)
        
        logger.info(f"内容拒绝成功: content_id={content_id}, reviewer_id={reviewer_id}")
        
        # TODO: 发送通知给创作者
        
        return content
    
    async def get_review_queue(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Content], int]:
        """
        获取审核队列
        
        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            
        Returns:
            tuple[List[Content], int]: (待审核内容列表, 总数)
        """
        from sqlalchemy import func
        
        # 查询总数
        count_result = await self.db.execute(
            select(func.count(Content.id)).where(
                Content.status == ContentStatus.UNDER_REVIEW
            )
        )
        total = count_result.scalar()
        
        # 查询待审核内容列表
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(Content)
            .where(Content.status == ContentStatus.UNDER_REVIEW)
            .order_by(Content.created_at.asc())  # 按提交时间升序
            .offset(offset)
            .limit(page_size)
        )
        contents = result.scalars().all()
        
        logger.info(f"审核队列查询成功: count={len(contents)}")
        
        return list(contents), total
    
    async def assign_expert_review(
        self,
        content_id: str,
        expert_id: str,
        assigner_id: str
    ) -> Content:
        """
        分配专家审核
        
        Args:
            content_id: 内容ID
            expert_id: 专家ID
            assigner_id: 分配人ID
            
        Returns:
            Content: 内容对象
            
        Raises:
            HTTPException: 内容不存在或状态不正确
        """
        from app.models.review_record import ReviewRecord
        
        # 查询内容
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "CONTENT_NOT_FOUND",
                    "message": "内容不存在"
                }
            )
        
        # 验证状态（必须是审核中）
        if content.status != ContentStatus.UNDER_REVIEW:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_STATUS",
                    "message": "只能为审核中的内容分配专家审核"
                }
            )
        
        # 创建专家审核记录
        review_record = ReviewRecord(
            id=str(uuid.uuid4()),
            content_id=content_id,
            reviewer_id=expert_id,
            review_type="expert_review",
            status="pending",
            created_at=datetime.utcnow()
        )
        
        self.db.add(review_record)
        await self.db.commit()
        await self.db.refresh(content)
        
        logger.info(f"专家审核分配成功: content_id={content_id}, expert_id={expert_id}")
        
        # TODO: 集成企业审批流程系统
        # TODO: 发送通知给专家
        
        return content
    
    async def expert_approve_content(
        self,
        content_id: str,
        expert_id: str,
        feedback: Optional[str] = None
    ) -> Content:
        """
        专家批准内容
        
        Args:
            content_id: 内容ID
            expert_id: 专家ID
            feedback: 专家反馈（可选）
            
        Returns:
            Content: 批准的内容对象
            
        Raises:
            HTTPException: 内容不存在或状态不正确
        """
        from app.models.review_record import ReviewRecord
        
        # 查询内容
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "CONTENT_NOT_FOUND",
                    "message": "内容不存在"
                }
            )
        
        # 验证状态
        if content.status != ContentStatus.UNDER_REVIEW:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_STATUS",
                    "message": "只能批准审核中的内容"
                }
            )
        
        # 查询专家审核记录
        review_result = await self.db.execute(
            select(ReviewRecord).where(
                ReviewRecord.content_id == content_id,
                ReviewRecord.reviewer_id == expert_id,
                ReviewRecord.review_type == "expert_review",
                ReviewRecord.status == "pending"
            )
        )
        review_record = review_result.scalar_one_or_none()
        
        if not review_record:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "REVIEW_RECORD_NOT_FOUND",
                    "message": "未找到待处理的专家审核记录"
                }
            )
        
        # 更新审核记录
        review_record.status = "approved"
        if feedback:
            review_record.reason = feedback
        
        # 更新内容状态为已发布
        content.status = ContentStatus.PUBLISHED
        content.published_at = datetime.utcnow()
        content.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(content)
        
        logger.info(f"专家批准内容成功: content_id={content_id}, expert_id={expert_id}")
        
        # TODO: 发送通知给创作者
        
        return content
    
    async def expert_reject_content(
        self,
        content_id: str,
        expert_id: str,
        feedback: str
    ) -> Content:
        """
        专家拒绝内容
        
        Args:
            content_id: 内容ID
            expert_id: 专家ID
            feedback: 专家反馈
            
        Returns:
            Content: 拒绝的内容对象
            
        Raises:
            HTTPException: 内容不存在或状态不正确
        """
        from app.models.review_record import ReviewRecord
        
        # 查询内容
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "CONTENT_NOT_FOUND",
                    "message": "内容不存在"
                }
            )
        
        # 验证状态
        if content.status != ContentStatus.UNDER_REVIEW:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_STATUS",
                    "message": "只能拒绝审核中的内容"
                }
            )
        
        # 验证反馈
        if not feedback or not feedback.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "FEEDBACK_REQUIRED",
                    "message": "专家反馈不能为空"
                }
            )
        
        # 查询专家审核记录
        review_result = await self.db.execute(
            select(ReviewRecord).where(
                ReviewRecord.content_id == content_id,
                ReviewRecord.reviewer_id == expert_id,
                ReviewRecord.review_type == "expert_review",
                ReviewRecord.status == "pending"
            )
        )
        review_record = review_result.scalar_one_or_none()
        
        if not review_record:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "REVIEW_RECORD_NOT_FOUND",
                    "message": "未找到待处理的专家审核记录"
                }
            )
        
        # 更新审核记录
        review_record.status = "rejected"
        review_record.reason = feedback
        
        # 更新内容状态为已驳回
        content.status = ContentStatus.REJECTED
        content.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(content)
        
        logger.info(f"专家拒绝内容成功: content_id={content_id}, expert_id={expert_id}")
        
        # TODO: 发送通知给创作者
        
        return content
    
    async def list_categories(self) -> List:
        """
        获取所有活动的内容分类
        
        Returns:
            List: 分类列表（包含层次结构）
        """
        from app.models.tag import Tag
        
        # 查询所有根分类（没有父分类的）
        result = await self.db.execute(
            select(Tag)
            .where(Tag.parent_id.is_(None))
            .order_by(Tag.name)
        )
        root_categories = result.scalars().all()
        
        logger.info(f"分类列表查询成功: count={len(root_categories)}")
        
        return list(root_categories)
    
    async def get_category_hierarchy(self, category_id: str) -> Optional:
        """
        获取分类的层次结构（包括子分类）
        
        Args:
            category_id: 分类ID
            
        Returns:
            Optional: 分类对象（包含子分类），不存在返回None
        """
        from app.models.tag import Tag
        
        result = await self.db.execute(
            select(Tag).where(Tag.id == category_id)
        )
        category = result.scalar_one_or_none()
        
        if category:
            logger.info(f"分类层次结构查询成功: category_id={category_id}")
        
        return category
    
    async def list_contents_by_category(
        self,
        category_id: str,
        page: int = 1,
        page_size: int = 20,
        include_subcategories: bool = True
    ) -> tuple[List[Content], int]:
        """
        按分类查询内容
        
        Args:
            category_id: 分类ID
            page: 页码（从1开始）
            page_size: 每页数量
            include_subcategories: 是否包含子分类的内容
            
        Returns:
            tuple[List[Content], int]: (内容列表, 总数)
        """
        from sqlalchemy import func
        from app.models.tag import Tag
        from app.models.content_tag import ContentTag
        
        # 获取分类ID列表（包括子分类）
        category_ids = [category_id]
        
        if include_subcategories:
            # 递归查询所有子分类
            async def get_subcategory_ids(parent_id: str) -> List[str]:
                result = await self.db.execute(
                    select(Tag.id).where(Tag.parent_id == parent_id)
                )
                subcategory_ids = [row[0] for row in result.all()]
                
                # 递归查询子分类的子分类
                for subcategory_id in subcategory_ids[:]:
                    subcategory_ids.extend(await get_subcategory_ids(subcategory_id))
                
                return subcategory_ids
            
            subcategory_ids = await get_subcategory_ids(category_id)
            category_ids.extend(subcategory_ids)
        
        # 查询总数
        count_result = await self.db.execute(
            select(func.count(func.distinct(Content.id)))
            .join(ContentTag, Content.id == ContentTag.content_id)
            .where(
                ContentTag.tag_id.in_(category_ids),
                Content.status == ContentStatus.PUBLISHED
            )
        )
        total = count_result.scalar()
        
        # 查询内容列表
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(Content)
            .join(ContentTag, Content.id == ContentTag.content_id)
            .where(
                ContentTag.tag_id.in_(category_ids),
                Content.status == ContentStatus.PUBLISHED
            )
            .distinct()
            .order_by(Content.published_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        contents = result.scalars().all()
        
        logger.info(f"按分类查询内容成功: category_id={category_id}, count={len(contents)}")
        
        return list(contents), total
    
    async def search_contents(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Content], int]:
        """
        搜索内容（全文搜索：标题、描述、标签）
        
        Args:
            query: 搜索关键词（多个关键词用空格分隔，使用OR逻辑）
            page: 页码（从1开始）
            page_size: 每页数量
            
        Returns:
            tuple[List[Content], int]: (内容列表, 总数)
        """
        from sqlalchemy import func, or_
        from app.models.tag import Tag
        from app.models.content_tag import ContentTag
        
        # 如果查询为空，返回空结果
        if not query or not query.strip():
            return [], 0
        
        # 分割关键词（多个关键词用空格分隔）
        keywords = query.strip().split()
        
        # 构建搜索条件（OR逻辑）
        search_conditions = []
        for keyword in keywords:
            keyword_pattern = f"%{keyword}%"
            search_conditions.append(Content.title.ilike(keyword_pattern))
            search_conditions.append(Content.description.ilike(keyword_pattern))
        
        # 查询总数
        count_result = await self.db.execute(
            select(func.count(func.distinct(Content.id)))
            .where(
                Content.status == ContentStatus.PUBLISHED,
                or_(*search_conditions)
            )
        )
        total = count_result.scalar()
        
        # 查询内容列表（按相关性排序 - 这里简化为按发布时间倒序）
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(Content)
            .where(
                Content.status == ContentStatus.PUBLISHED,
                or_(*search_conditions)
            )
            .distinct()
            .order_by(Content.published_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        contents = result.scalars().all()
        
        logger.info(f"内容搜索成功: query={query}, count={len(contents)}")
        
        return list(contents), total
    
    async def get_user_contents(
        self,
        user_id: str,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Content], int]:
        """
        获取用户的内容列表（我的发布）
        
        Args:
            user_id: 用户ID
            status: 内容状态筛选（draft, under_review, approved, rejected, published, removed）
            page: 页码
            page_size: 每页数量
            
        Returns:
            内容列表和总数
        """
        # 构建查询
        query = select(Content).where(Content.creator_id == user_id)
        
        # 状态筛选
        if status:
            query = query.where(Content.status == status)
        
        # 按创建时间倒序排序
        query = query.order_by(Content.created_at.desc())
        
        # 计算总数
        count_query = select(func.count()).select_from(Content).where(Content.creator_id == user_id)
        if status:
            count_query = count_query.where(Content.status == status)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # 执行查询
        result = await self.db.execute(query)
        contents = result.scalars().all()
        
        return list(contents), total
    
    async def resubmit_content(
        self,
        content_id: str,
        user_id: str
    ) -> Content:
        """
        重新提交被驳回的内容
        
        Args:
            content_id: 内容ID
            user_id: 用户ID
            
        Returns:
            更新后的内容
            
        Raises:
            ValueError: 内容不存在、不属于该用户或状态不允许重新提交
        """
        # 获取内容
        content = await self.get_content(content_id)
        
        if not content:
            raise ValueError("内容不存在")
        
        if content.creator_id != user_id:
            raise ValueError("无权操作此内容")
        
        # 只有草稿和已驳回的内容可以重新提交
        if content.status not in ["draft", "rejected"]:
            raise ValueError(f"当前状态（{content.status}）不允许重新提交")
        
        # 更新状态为审核中
        content.status = "under_review"
        content.updated_at = datetime.utcnow()
        
        # 创建审核记录
        review_record = ReviewRecord(
            id=str(uuid.uuid4()),
            content_id=content_id,
            reviewer_id=None,  # 待分配审核员
            review_type="platform_review",
            status="pending",
            created_at=datetime.utcnow()
        )
        
        self.db.add(review_record)
        await self.db.commit()
        await self.db.refresh(content)
        
        # TODO: 发送通知给审核员
        
        return content
    
    async def filter_contents(
        self,
        content_type: Optional[List[str]] = None,
        position: Optional[List[str]] = None,
        skill: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        creator_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Content], int]:
        """
        多维内容筛选（使用AND逻辑）
        
        Args:
            content_type: 内容类型列表
            position: 岗位列表
            skill: 技能列表
            tags: 标签列表
            creator_id: 创作者ID
            page: 页码（从1开始）
            page_size: 每页数量
            
        Returns:
            tuple[List[Content], int]: (内容列表, 总数)
        """
        from sqlalchemy import func, and_
        from app.models.tag import Tag
        from app.models.content_tag import ContentTag
        
        # 构建筛选条件（AND逻辑）
        filter_conditions = [Content.status == ContentStatus.PUBLISHED]
        
        # 内容类型筛选
        if content_type:
            filter_conditions.append(Content.content_type.in_(content_type))
        
        # 创作者筛选
        if creator_id:
            filter_conditions.append(Content.creator_id == creator_id)
        
        # 构建基础查询
        query = select(Content).where(and_(*filter_conditions))
        
        # 标签筛选（需要join ContentTag表）
        if tags or position or skill:
            # 获取所有相关标签ID
            tag_names = []
            if tags:
                tag_names.extend(tags)
            if position:
                tag_names.extend(position)
            if skill:
                tag_names.extend(skill)
            
            # 查询标签ID
            tag_result = await self.db.execute(
                select(Tag.id).where(Tag.name.in_(tag_names))
            )
            tag_ids = [row[0] for row in tag_result.all()]
            
            if tag_ids:
                # 对于每个标签，内容必须都包含（AND逻辑）
                for tag_id in tag_ids:
                    query = query.join(
                        ContentTag,
                        and_(
                            Content.id == ContentTag.content_id,
                            ContentTag.tag_id == tag_id
                        )
                    )
        
        # 查询总数
        count_query = select(func.count(func.distinct(Content.id))).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # 如果没有结果，直接返回
        if total == 0:
            return [], 0
        
        # 查询内容列表
        offset = (page - 1) * page_size
        query = query.distinct().order_by(Content.published_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        contents = result.scalars().all()
        
        logger.info(f"内容筛选成功: filters={{'content_type': {content_type}, 'tags': {tags}}}, count={len(contents)}")
        
        return list(contents), total

    
    # ==================== 管理后台方法 ====================
    
    async def admin_list_contents(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[dict] = None
    ) -> tuple[List[Content], int]:
        """
        管理员查询所有内容列表（支持筛选和搜索）
        
        需求：38.1-38.4
        
        Args:
            page: 页码
            page_size: 每页数量
            search: 搜索关键词
            filters: 筛选条件字典
            
        Returns:
            tuple[List[Content], int]: (内容列表, 总数)
        """
        from sqlalchemy import func, and_, or_
        
        # 构建筛选条件
        filter_conditions = []
        
        if filters:
            # 状态筛选
            if filters.get('status'):
                filter_conditions.append(Content.status == filters['status'])
            
            # 内容类型筛选
            if filters.get('content_type'):
                filter_conditions.append(Content.content_type == filters['content_type'])
            
            # 创作者筛选
            if filters.get('creator_id'):
                filter_conditions.append(Content.creator_id == filters['creator_id'])
            
            # 日期范围筛选
            if filters.get('start_date'):
                start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d')
                filter_conditions.append(Content.created_at >= start_date)
            
            if filters.get('end_date'):
                end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d')
                # 包含结束日期的全天
                end_date = end_date.replace(hour=23, minute=59, second=59)
                filter_conditions.append(Content.created_at <= end_date)
        
        # 搜索条件（标题或描述包含关键词）
        if search:
            search_condition = or_(
                Content.title.contains(search),
                Content.description.contains(search)
            )
            filter_conditions.append(search_condition)
        
        # 构建查询
        if filter_conditions:
            query = select(Content).where(and_(*filter_conditions))
        else:
            query = select(Content)
        
        # 查询总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # 查询内容列表
        offset = (page - 1) * page_size
        query = query.order_by(Content.created_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        contents = result.scalars().all()
        
        logger.info(f"管理员查询内容列表: page={page}, total={total}")
        
        return list(contents), total
    
    async def admin_batch_operation(
        self,
        operation_type: str,
        content_ids: List[str],
        admin_id: str,
        reason: Optional[str] = None
    ) -> dict:
        """
        管理员批量操作内容
        
        需求：38.4
        
        Args:
            operation_type: 操作类型（approve, reject, remove, feature, unfeature）
            content_ids: 内容ID列表
            admin_id: 管理员ID
            reason: 操作原因
            
        Returns:
            dict: 操作结果 {'success': [...], 'failed': [...]}
        """
        success = []
        failed = []
        
        for content_id in content_ids:
            try:
                content = await self.get_content(content_id)
                
                if not content:
                    failed.append({
                        'content_id': content_id,
                        'reason': '内容不存在'
                    })
                    continue
                
                # 根据操作类型执行相应操作
                if operation_type == 'approve':
                    await self.approve_content(content_id, admin_id)
                elif operation_type == 'reject':
                    await self.reject_content(content_id, admin_id, reason or '管理员批量拒绝')
                elif operation_type == 'remove':
                    await self.admin_remove_content(content_id, admin_id, reason or '管理员批量下架')
                elif operation_type == 'feature':
                    await self.admin_feature_content(content_id, True)
                elif operation_type == 'unfeature':
                    await self.admin_feature_content(content_id, False)
                else:
                    failed.append({
                        'content_id': content_id,
                        'reason': f'不支持的操作类型: {operation_type}'
                    })
                    continue
                
                success.append(content_id)
                
            except Exception as e:
                logger.error(f"批量操作失败: content_id={content_id}, error={str(e)}")
                failed.append({
                    'content_id': content_id,
                    'reason': str(e)
                })
        
        logger.info(f"批量操作完成: operation={operation_type}, success={len(success)}, failed={len(failed)}")
        
        return {
            'success': success,
            'failed': failed
        }
    
    async def admin_get_content_detail(self, content_id: str) -> Optional[Content]:
        """
        管理员获取内容详情（包括AI分析结果、审核记录等）
        
        需求：38.1
        
        Args:
            content_id: 内容ID
            
        Returns:
            Optional[Content]: 内容对象
        """
        from sqlalchemy.orm import selectinload
        from app.models.review_record import ReviewRecord
        
        # 查询内容及关联数据
        query = select(Content).where(Content.id == content_id).options(
            selectinload(Content.tags)
        )
        
        result = await self.db.execute(query)
        content = result.scalar_one_or_none()
        
        return content
    
    async def admin_get_content_statistics(self) -> dict:
        """
        获取内容统计信息
        
        需求：38.1
        
        Returns:
            dict: 统计数据
        """
        from sqlalchemy import func
        from datetime import date
        
        # 查询各状态内容数量
        status_query = select(
            Content.status,
            func.count(Content.id).label('count')
        ).group_by(Content.status)
        
        status_result = await self.db.execute(status_query)
        status_counts = {row[0]: row[1] for row in status_result.all()}
        
        # 查询总数
        total_query = select(func.count(Content.id))
        total_result = await self.db.execute(total_query)
        total = total_result.scalar()
        
        # 查询今日新增
        today = date.today()
        today_query = select(func.count(Content.id)).where(
            func.date(Content.created_at) == today
        )
        today_result = await self.db.execute(today_query)
        today_new = today_result.scalar()
        
        # 查询今日发布
        today_published_query = select(func.count(Content.id)).where(
            and_(
                Content.status == ContentStatus.PUBLISHED,
                func.date(Content.published_at) == today
            )
        )
        today_published_result = await self.db.execute(today_published_query)
        today_published = today_published_result.scalar()
        
        return {
            'total_contents': total,
            'draft_count': status_counts.get('draft', 0),
            'under_review_count': status_counts.get('under_review', 0),
            'published_count': status_counts.get('published', 0),
            'rejected_count': status_counts.get('rejected', 0),
            'removed_count': status_counts.get('removed', 0),
            'today_new_count': today_new,
            'today_published_count': today_published
        }
    
    async def admin_remove_content(
        self,
        content_id: str,
        admin_id: str,
        reason: str,
        create_audit_log: bool = True
    ) -> Content:
        """
        管理员下架内容
        
        需求：40.1-40.4
        
        Args:
            content_id: 内容ID
            admin_id: 管理员ID
            reason: 下架原因
            create_audit_log: 是否创建审计日志
            
        Returns:
            Content: 更新后的内容
        """
        content = await self.get_content(content_id)
        
        if not content:
            raise ValueError("内容不存在")
        
        # 更新状态为已下架
        content.status = ContentStatus.REMOVED
        content.updated_at = datetime.utcnow()
        
        # 创建审核记录（审计日志）
        if create_audit_log:
            review_record = ReviewRecord(
                id=str(uuid.uuid4()),
                content_id=content_id,
                reviewer_id=admin_id,
                review_type="admin_remove",
                status="removed",
                reason=reason,
                created_at=datetime.utcnow()
            )
            
            self.db.add(review_record)
        
        await self.db.commit()
        await self.db.refresh(content)
        
        logger.info(f"管理员下架内容: content_id={content_id}, admin_id={admin_id}, reason={reason}")
        
        return content
    
    async def get_content_audit_logs(self, content_id: str) -> List:
        """
        获取内容的审计日志
        
        需求：40.4
        
        Args:
            content_id: 内容ID
            
        Returns:
            List[ReviewRecord]: 审计日志列表
        """
        from app.models.review_record import ReviewRecord
        
        # 验证内容存在
        content = await self.get_content(content_id)
        if not content:
            raise ValueError("内容不存在")
        
        # 查询审核记录
        query = select(ReviewRecord).where(
            ReviewRecord.content_id == content_id
        ).order_by(ReviewRecord.created_at.desc())
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return list(logs)
    
    async def admin_restore_content(
        self,
        content_id: str,
        admin_id: str
    ) -> Content:
        """
        管理员恢复已下架的内容
        
        需求：40.1
        
        Args:
            content_id: 内容ID
            admin_id: 管理员ID
            
        Returns:
            Content: 恢复后的内容
        """
        content = await self.get_content(content_id)
        
        if not content:
            raise ValueError("内容不存在")
        
        if content.status != ContentStatus.REMOVED:
            raise ValueError("只能恢复已下架的内容")
        
        # 恢复为已发布状态
        content.status = ContentStatus.PUBLISHED
        content.updated_at = datetime.utcnow()
        
        # 创建审核记录
        review_record = ReviewRecord(
            id=str(uuid.uuid4()),
            content_id=content_id,
            reviewer_id=admin_id,
            review_type="admin_restore",
            status="approved",
            reason="管理员恢复内容",
            created_at=datetime.utcnow()
        )
        
        self.db.add(review_record)
        await self.db.commit()
        await self.db.refresh(content)
        
        logger.info(f"管理员恢复内容: content_id={content_id}, admin_id={admin_id}")
        
        return content
    
    async def admin_feature_content(
        self,
        content_id: str,
        is_featured: bool,
        priority: Optional[int] = None,
        featured_position: Optional[str] = None
    ) -> Content:
        """
        管理员设置精选内容
        
        需求：41.1-41.4
        
        Args:
            content_id: 内容ID
            is_featured: 是否精选
            priority: 显示优先级
            featured_position: 精选位置
            
        Returns:
            Content: 更新后的内容
        """
        content = await self.get_content(content_id)
        
        if not content:
            raise ValueError("内容不存在")
        
        # 只有已发布的内容可以设置为精选
        if is_featured and content.status != ContentStatus.PUBLISHED:
            raise ValueError("只有已发布的内容可以设置为精选")
        
        # 更新精选状态（使用整数：0=否，1=是）
        content.is_featured = 1 if is_featured else 0
        
        # 更新优先级
        if priority is not None:
            content.featured_priority = priority
        elif is_featured and content.featured_priority == 0:
            # 如果设置为精选但没有指定优先级，默认设置为50
            content.featured_priority = 50
        
        # 更新精选位置
        if featured_position is not None:
            content.featured_position = featured_position
        
        content.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(content)
        
        logger.info(f"管理员设置精选内容: content_id={content_id}, is_featured={is_featured}")
        
        return content

    
    async def admin_upload_video(
        self,
        file: UploadFile,
        admin_id: str,
        metadata: VideoMetadataCreate,
        auto_publish: bool = True
    ) -> Content:
        """
        管理员上传视频（支持自动发布）
        
        需求：39.1-39.4
        
        Args:
            file: 上传的视频文件
            admin_id: 管理员ID
            metadata: 视频元数据
            auto_publish: 是否自动发布（跳过审核）
            
        Returns:
            Content: 创建的内容对象
        """
        # 验证视频格式
        if not self._validate_video_format(file.filename):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "VIDEO_FORMAT_UNSUPPORTED",
                    "message": f"不支持的视频格式，请上传{', '.join(self.SUPPORTED_VIDEO_FORMATS)}格式的视频",
                    "details": {
                        "uploaded_format": file.filename.rsplit('.', 1)[-1] if '.' in file.filename else 'unknown',
                        "supported_formats": self.SUPPORTED_VIDEO_FORMATS
                    }
                }
            )
        
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 验证文件大小
        if not self._validate_file_size(file_size):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "FILE_SIZE_EXCEEDED",
                    "message": f"文件大小超过限制，最大允许{self.MAX_VIDEO_SIZE // (1024 * 1024)}MB",
                    "details": {
                        "file_size": file_size,
                        "max_size": self.MAX_VIDEO_SIZE
                    }
                }
            )
        
        # 创建内容记录
        content_id = str(uuid.uuid4())
        
        # 上传到存储
        # 将字节内容包装为类文件对象
        from io import BytesIO
        file_obj = BytesIO(file_content)
        video_url = await self.storage.upload_file(
            file=file_obj,
            filename=file.filename,
            file_type="videos",
            user_id=admin_id
        )
        
        # 获取视频时长（如果可能）
        duration = None
        try:
            # 保存临时文件以获取时长
            temp_path = f"/tmp/{content_id}_{file.filename}"
            with open(temp_path, 'wb') as f:
                f.write(file_content)
            
            duration = await self._get_video_duration(temp_path)
            
            # 删除临时文件
            os.remove(temp_path)
        except Exception as e:
            logger.warning(f"获取视频时长失败: {str(e)}")
        
        # 确定内容状态
        if auto_publish:
            status = ContentStatus.PUBLISHED
            published_at = datetime.utcnow()
        else:
            status = ContentStatus.DRAFT
            published_at = None
        
        # 创建内容对象
        content = Content(
            id=content_id,
            title=metadata.title,
            description=metadata.description,
            video_url=video_url,
            duration=duration,
            file_size=file_size,
            creator_id=admin_id,
            status=status,
            content_type=metadata.content_type,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            published_at=published_at
        )
        
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)
        
        # 如果有自定义标签，添加标签
        if metadata.tags:
            await self._add_custom_tags(content_id, metadata.tags)
        
        # 如果自动发布，创建审核记录
        if auto_publish:
            review_record = ReviewRecord(
                id=str(uuid.uuid4()),
                content_id=content_id,
                reviewer_id=admin_id,
                review_type="admin_upload",
                status="approved",
                reason="管理员上传自动发布",
                created_at=datetime.utcnow()
            )
            self.db.add(review_record)
            await self.db.commit()
        
        logger.info(f"管理员上传视频成功: content_id={content_id}, admin_id={admin_id}, auto_publish={auto_publish}")
        
        return content

    
    async def create_content_from_uploaded_file(
        self,
        admin_id: str,
        video_url: str,
        title: str,
        description: Optional[str],
        content_type: str,
        tag_ids: List[str],
        cover_url: Optional[str] = None,
        auto_publish: bool = True,
        is_featured: bool = False,
        priority: int = 0
    ) -> Content:
        """
        从已上传的文件创建内容记录
        
        Args:
            admin_id: 管理员ID
            video_url: 视频URL（已上传）
            title: 标题
            description: 描述
            content_type: 内容类型
            tag_ids: 标签ID列表
            cover_url: 封面URL（可选）
            auto_publish: 是否自动发布
            is_featured: 是否精选
            priority: 优先级
            
        Returns:
            Content: 创建的内容对象
        """
        # 创建内容记录
        content_id = str(uuid.uuid4())
        
        # 确定内容状态
        if auto_publish:
            status = ContentStatus.PUBLISHED
            published_at = datetime.utcnow()
        else:
            status = ContentStatus.DRAFT
            published_at = None
        
        # 创建内容对象
        content = Content(
            id=content_id,
            title=title,
            description=description,
            video_url=video_url,
            cover_url=cover_url,
            creator_id=admin_id,
            status=status,
            content_type=content_type,
            is_featured=1 if is_featured else 0,
            featured_priority=priority if is_featured else 0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            published_at=published_at
        )
        
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)
        
        # 添加标签关联
        if tag_ids:
            for tag_id in tag_ids:
                content_tag = ContentTag(
                    id=str(uuid.uuid4()),
                    content_id=content_id,
                    tag_id=tag_id
                )
                self.db.add(content_tag)
            await self.db.commit()
        
        # 如果自动发布，创建审核记录
        if auto_publish:
            review_record = ReviewRecord(
                id=str(uuid.uuid4()),
                content_id=content_id,
                reviewer_id=admin_id,
                review_type="admin_upload",
                status="approved",
                reason="管理员上传自动发布",
                created_at=datetime.utcnow()
            )
            self.db.add(review_record)
            await self.db.commit()
        
        logger.info(f"管理员创建内容成功: content_id={content_id}, admin_id={admin_id}, auto_publish={auto_publish}")
        
        # 重新加载内容以包含creator关系
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(Content).options(selectinload(Content.creator)).where(Content.id == content_id)
        )
        content = result.scalar_one()
        
        return content

    
    async def list_featured_contents(
        self,
        page: int = 1,
        page_size: int = 20,
        featured_position: Optional[str] = None
    ) -> tuple[List[Content], int]:
        """
        获取精选内容列表
        
        需求：41.2
        
        Args:
            page: 页码
            page_size: 每页数量
            featured_position: 精选位置筛选
            
        Returns:
            tuple[List[Content], int]: (内容列表, 总数)
        """
        from sqlalchemy import func, and_
        
        # 构建筛选条件
        filter_conditions = [
            Content.status == ContentStatus.PUBLISHED,
            Content.is_featured == 1  # 精选内容
        ]
        
        # 精选位置筛选
        if featured_position and hasattr(Content, 'featured_position'):
            filter_conditions.append(Content.featured_position == featured_position)
        
        # 构建查询
        query = select(Content).where(and_(*filter_conditions))
        
        # 查询总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # 查询内容列表（按优先级排序）
        offset = (page - 1) * page_size
        
        # 如果有featured_priority字段，按优先级排序
        if hasattr(Content, 'featured_priority'):
            query = query.order_by(
                Content.featured_priority.desc(),
                Content.published_at.desc()
            )
        else:
            query = query.order_by(Content.published_at.desc())
        
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        contents = result.scalars().all()
        
        logger.info(f"查询精选内容列表: page={page}, total={total}")
        
        return list(contents), total
    
    async def update_featured_priority(
        self,
        content_id: str,
        priority: int
    ) -> Content:
        """
        更新精选内容的显示优先级
        
        需求：41.3
        
        Args:
            content_id: 内容ID
            priority: 显示优先级
            
        Returns:
            Content: 更新后的内容
        """
        content = await self.get_content(content_id)
        
        if not content:
            raise ValueError("内容不存在")
        
        # 检查是否为精选内容
        if content.is_featured != 1:
            raise ValueError("只能更新精选内容的优先级")
        
        # 更新优先级
        content.featured_priority = priority
        content.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(content)
        
        logger.info(f"更新精选内容优先级: content_id={content_id}, priority={priority}")
        
        return content

    
    async def get_content_review_detail(self, content_id: str) -> dict:
        """
        获取内容审核详情（包括审核记录和AI分析结果）
        
        需求：42.2
        
        Args:
            content_id: 内容ID
            
        Returns:
            dict: 包含content和review_records的字典
        """
        from app.models.review_record import ReviewRecord
        from app.models.user import User
        
        # 查询内容
        content = await self.get_content(content_id)
        if not content:
            raise ValueError("内容不存在")
        
        # 查询审核记录
        query = select(ReviewRecord, User).join(
            User, ReviewRecord.reviewer_id == User.id
        ).where(
            ReviewRecord.content_id == content_id
        ).order_by(ReviewRecord.created_at.desc())
        
        result = await self.db.execute(query)
        records = result.all()
        
        review_records = []
        for record, reviewer in records:
            review_records.append({
                'id': record.id,
                'content_id': record.content_id,
                'reviewer_id': record.reviewer_id,
                'reviewer_name': reviewer.name,
                'review_type': record.review_type,
                'status': record.status,
                'reason': record.reason,
                'created_at': record.created_at
            })
        
        return {
            'content': content,
            'review_records': review_records
        }
    
    async def get_review_statistics(self) -> dict:
        """
        获取审核统计信息
        
        需求：42.1
        
        Returns:
            dict: 审核统计数据
        """
        from app.models.review_record import ReviewRecord
        from sqlalchemy import func, and_
        
        # 待审核数量
        pending_query = select(func.count(Content.id)).where(
            Content.status == ContentStatus.UNDER_REVIEW
        )
        pending_result = await self.db.execute(pending_query)
        pending_count = pending_result.scalar() or 0
        
        # 今日审核数量
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_query = select(func.count(ReviewRecord.id)).where(
            and_(
                ReviewRecord.created_at >= today_start,
                ReviewRecord.review_type == "platform_review"
            )
        )
        today_result = await self.db.execute(today_query)
        today_count = today_result.scalar() or 0
        
        # 今日批准数量
        today_approved_query = select(func.count(ReviewRecord.id)).where(
            and_(
                ReviewRecord.created_at >= today_start,
                ReviewRecord.status == "approved",
                ReviewRecord.review_type == "platform_review"
            )
        )
        today_approved_result = await self.db.execute(today_approved_query)
        today_approved_count = today_approved_result.scalar() or 0
        
        # 今日拒绝数量
        today_rejected_query = select(func.count(ReviewRecord.id)).where(
            and_(
                ReviewRecord.created_at >= today_start,
                ReviewRecord.status == "rejected",
                ReviewRecord.review_type == "platform_review"
            )
        )
        today_rejected_result = await self.db.execute(today_rejected_query)
        today_rejected_count = today_rejected_result.scalar() or 0
        
        # 本周审核数量
        week_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = week_start - timedelta(days=week_start.weekday())
        week_query = select(func.count(ReviewRecord.id)).where(
            and_(
                ReviewRecord.created_at >= week_start,
                ReviewRecord.review_type == "platform_review"
            )
        )
        week_result = await self.db.execute(week_query)
        week_count = week_result.scalar() or 0
        
        # 按内容类型统计待审核数量
        type_query = select(
            Content.content_type,
            func.count(Content.id).label('count')
        ).where(
            Content.status == ContentStatus.UNDER_REVIEW
        ).group_by(Content.content_type)
        
        type_result = await self.db.execute(type_query)
        type_stats = {row.content_type: row.count for row in type_result}
        
        return {
            'pending_count': pending_count,
            'today_count': today_count,
            'today_approved_count': today_approved_count,
            'today_rejected_count': today_rejected_count,
            'week_count': week_count,
            'by_content_type': type_stats
        }

    async def admin_update_content(
        self,
        content_id: str,
        admin_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        content_type: Optional[str] = None,
        tag_ids: Optional[List[str]] = None,
        video_url: Optional[str] = None,
        cover_url: Optional[str] = None,
        is_featured: Optional[bool] = None,
        priority: Optional[int] = None
    ) -> Content:
        """
        管理员更新内容信息
        
        Args:
            content_id: 内容ID
            admin_id: 管理员ID
            title: 标题
            description: 描述
            content_type: 内容类型
            tag_ids: 标签ID列表
            video_url: 视频URL
            cover_url: 封面URL
            is_featured: 是否精选
            priority: 优先级
            
        Returns:
            Content: 更新后的内容对象
            
        Raises:
            ValueError: 内容不存在
        """
        from sqlalchemy import delete as sql_delete
        from sqlalchemy.orm import selectinload
        
        content = await self.get_content(content_id)
        
        if not content:
            raise ValueError("内容不存在")
        
        # 更新字段
        if title is not None:
            content.title = title
        if description is not None:
            content.description = description
        if content_type is not None:
            content.content_type = content_type
        if video_url is not None:
            content.video_url = video_url
        if cover_url is not None:
            content.cover_url = cover_url
        if is_featured is not None:
            content.is_featured = 1 if is_featured else 0
        if priority is not None:
            content.featured_priority = priority
        
        content.updated_at = datetime.utcnow()
        
        # 更新标签关联
        if tag_ids is not None:
            # 删除旧的标签关联
            await self.db.execute(
                sql_delete(ContentTag).where(ContentTag.content_id == content_id)
            )
            
            # 添加新的标签关联
            for tag_id in tag_ids:
                content_tag = ContentTag(
                    id=str(uuid.uuid4()),
                    content_id=content_id,
                    tag_id=tag_id
                )
                self.db.add(content_tag)
        
        await self.db.commit()
        await self.db.refresh(content)
        
        logger.info(f"管理员更新内容: content_id={content_id}, admin_id={admin_id}")
        
        # 重新加载内容以包含creator关系
        result = await self.db.execute(
            select(Content).options(selectinload(Content.creator)).where(Content.id == content_id)
        )
        content = result.scalar_one()
        
        return content

    async def admin_delete_content(
        self,
        content_id: str,
        admin_id: str
    ) -> None:
        """
        管理员删除内容（物理删除）
        
        Args:
            content_id: 内容ID
            admin_id: 管理员ID
            
        Raises:
            ValueError: 内容不存在
        """
        from sqlalchemy import delete as sql_delete
        
        content = await self.get_content(content_id)
        
        if not content:
            raise ValueError("内容不存在")
        
        # 删除相关的标签关联
        await self.db.execute(
            sql_delete(ContentTag).where(ContentTag.content_id == content_id)
        )
        
        # 删除相关的审核记录
        await self.db.execute(
            sql_delete(ReviewRecord).where(ReviewRecord.content_id == content_id)
        )
        
        # 删除内容本身
        await self.db.delete(content)
        await self.db.commit()
        
        logger.info(f"管理员删除内容: content_id={content_id}, admin_id={admin_id}")
