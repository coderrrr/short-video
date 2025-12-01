"""
内容服务测试
"""
import pytest
from io import BytesIO
from fastapi import UploadFile, HTTPException

from app.services.content_service import ContentService
from app.schemas.content_schemas import VideoMetadataCreate, VideoMetadataUpdate
from app.models.user import User
from app.models.content import Content, ContentStatus


@pytest.fixture
async def test_user(db_session):
    """创建测试用户"""
    user = User(
        id="test-user-1",
        employee_id="EMP001",
        name="测试用户",
        department="技术部",
        position="工程师"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestContentService:
    """内容服务测试类"""
    
    @pytest.mark.asyncio
    async def test_validate_video_format(self, db_session):
        """测试视频格式验证"""
        service = ContentService(db_session)
        
        # 测试支持的格式
        assert service._validate_video_format("test.mp4") is True
        assert service._validate_video_format("test.mov") is True
        assert service._validate_video_format("test.avi") is True
        assert service._validate_video_format("TEST.MP4") is True
        
        # 测试不支持的格式
        assert service._validate_video_format("test.wmv") is False
        assert service._validate_video_format("test.flv") is False
        assert service._validate_video_format("test.mkv") is False
        assert service._validate_video_format("test") is False
    
    @pytest.mark.asyncio
    async def test_validate_image_format(self, db_session):
        """测试图片格式验证"""
        service = ContentService(db_session)
        
        # 测试支持的格式
        assert service._validate_image_format("test.jpg") is True
        assert service._validate_image_format("test.jpeg") is True
        assert service._validate_image_format("test.png") is True
        assert service._validate_image_format("TEST.JPG") is True
        
        # 测试不支持的格式
        assert service._validate_image_format("test.gif") is False
        assert service._validate_image_format("test.bmp") is False
        assert service._validate_image_format("test") is False
    
    @pytest.mark.asyncio
    async def test_validate_file_size(self, db_session):
        """测试文件大小验证"""
        service = ContentService(db_session)
        
        # 测试符合要求的大小
        assert service._validate_file_size(100 * 1024 * 1024) is True  # 100MB
        assert service._validate_file_size(500 * 1024 * 1024) is True  # 500MB
        
        # 测试超过限制的大小
        assert service._validate_file_size(600 * 1024 * 1024) is False  # 600MB
        assert service._validate_file_size(1000 * 1024 * 1024) is False  # 1GB
    
    @pytest.mark.asyncio
    async def test_upload_video_unsupported_format(self, db_session, test_user):
        """测试上传不支持的视频格式"""
        service = ContentService(db_session)
        
        # 创建一个不支持格式的文件
        file_content = b"fake video content"
        file = UploadFile(
            filename="test.wmv",
            file=BytesIO(file_content)
        )
        
        metadata = VideoMetadataCreate(
            title="测试视频",
            description="测试描述",
            content_type="工作知识",
            tags=["测试"]
        )
        
        # 应该抛出HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_video(file, test_user.id, metadata)
        
        assert exc_info.value.status_code == 400
        assert "VIDEO_FORMAT_UNSUPPORTED" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_upload_video_exceeds_size_limit(self, db_session, test_user):
        """测试上传超大视频"""
        service = ContentService(db_session)
        
        # 创建一个超大文件（模拟）
        file_content = b"x" * (600 * 1024 * 1024)  # 600MB
        file = UploadFile(
            filename="test.mp4",
            file=BytesIO(file_content)
        )
        
        metadata = VideoMetadataCreate(
            title="测试视频",
            description="测试描述",
            content_type="工作知识",
            tags=["测试"]
        )
        
        # 应该抛出HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_video(file, test_user.id, metadata)
        
        assert exc_info.value.status_code == 400
        assert "FILE_SIZE_EXCEEDED" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_update_metadata_title_validation(self, db_session, test_user):
        """测试元数据标题验证"""
        # 创建一个测试内容
        content = Content(
            id="test-content-1",
            title="原始标题",
            description="原始描述",
            video_url="http://example.com/video.mp4",
            creator_id=test_user.id,
            status=ContentStatus.DRAFT,
            content_type="工作知识"
        )
        db_session.add(content)
        await db_session.commit()
        
        service = ContentService(db_session)
        
        # 测试空标题
        metadata = VideoMetadataUpdate(title="")
        with pytest.raises(HTTPException):
            await service.update_metadata(content.id, test_user.id, metadata)
        
        # 测试仅空白字符的标题
        metadata = VideoMetadataUpdate(title="   ")
        with pytest.raises(HTTPException):
            await service.update_metadata(content.id, test_user.id, metadata)
    
    @pytest.mark.asyncio
    async def test_update_metadata_under_review_blocked(self, db_session, test_user):
        """测试审核中的内容不可编辑"""
        # 创建一个审核中的内容
        content = Content(
            id="test-content-2",
            title="审核中的内容",
            description="描述",
            video_url="http://example.com/video.mp4",
            creator_id=test_user.id,
            status=ContentStatus.UNDER_REVIEW,
            content_type="工作知识"
        )
        db_session.add(content)
        await db_session.commit()
        
        service = ContentService(db_session)
        
        # 尝试更新元数据
        metadata = VideoMetadataUpdate(title="新标题")
        with pytest.raises(HTTPException) as exc_info:
            await service.update_metadata(content.id, test_user.id, metadata)
        
        assert exc_info.value.status_code == 400
        assert "CONTENT_UNDER_REVIEW" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_update_metadata_permission_denied(self, db_session, test_user):
        """测试无权限修改他人内容"""
        # 创建另一个用户的内容
        other_user = User(
            id="other-user",
            employee_id="EMP002",
            name="其他用户",
            department="技术部",
            position="工程师"
        )
        db_session.add(other_user)
        
        content = Content(
            id="test-content-3",
            title="他人的内容",
            description="描述",
            video_url="http://example.com/video.mp4",
            creator_id=other_user.id,
            status=ContentStatus.DRAFT,
            content_type="工作知识"
        )
        db_session.add(content)
        await db_session.commit()
        
        service = ContentService(db_session)
        
        # 尝试用test_user更新other_user的内容
        metadata = VideoMetadataUpdate(title="新标题")
        with pytest.raises(HTTPException) as exc_info:
            await service.update_metadata(content.id, test_user.id, metadata)
        
        assert exc_info.value.status_code == 403
        assert "PERMISSION_DENIED" in str(exc_info.value.detail)
