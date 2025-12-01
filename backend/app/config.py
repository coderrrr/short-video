"""
应用配置管理
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Union
from pydantic import field_validator


class Settings(BaseSettings):
    """应用配置"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # 应用基础配置
    APP_NAME: str = "企业内部短视频平台"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # 数据库配置
    DATABASE_URL: str = "mysql+aiomysql://short_video_user:short_video_pass@localhost:3306/short_video"
    
    # 存储配置
    STORAGE_TYPE: str = "local"  # local 或 s3
    LOCAL_STORAGE_PATH: str = "./storage"
    
    # S3配置（生产环境）
    S3_BUCKET_NAME: Optional[str] = None
    S3_REGION: Optional[str] = "cn-northwest-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # 文件上传限制
    MAX_VIDEO_SIZE_MB: int = 500
    SUPPORTED_VIDEO_FORMATS: Union[str, list[str]] = "mp4,mov,avi"
    
    # JWT配置
    JWT_SECRET_KEY: str = "your-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    
    @field_validator('SUPPORTED_VIDEO_FORMATS', mode='after')
    @classmethod
    def parse_video_formats(cls, v):
        """解析视频格式列表，支持逗号分隔的字符串"""
        if isinstance(v, str):
            # 处理空字符串
            if not v.strip():
                return ["mp4", "mov", "avi"]
            return [fmt.strip() for fmt in v.split(',') if fmt.strip()]
        if isinstance(v, list):
            return v
        # 默认值
        return ["mp4", "mov", "avi"]


settings = Settings()
