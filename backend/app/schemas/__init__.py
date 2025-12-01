# Pydantic数据模式

from app.schemas.user_schemas import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
    LoginResponse,
    TokenData,
    KOLStatusUpdate,
)

from app.schemas.content_schemas import (
    ContentStatus,
    VideoMetadataCreate,
    VideoMetadataUpdate,
    FileUploadResponse,
    VideoUploadResponse,
    ContentResponse,
    CoverImageUploadResponse,
    VideoEditRequest,
    VideoFrameExtractRequest,
)

__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "LoginRequest",
    "LoginResponse",
    "TokenData",
    "KOLStatusUpdate",
    "ContentStatus",
    "VideoMetadataCreate",
    "VideoMetadataUpdate",
    "FileUploadResponse",
    "VideoUploadResponse",
    "ContentResponse",
    "CoverImageUploadResponse",
    "VideoEditRequest",
    "VideoFrameExtractRequest",
]
