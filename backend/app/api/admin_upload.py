"""
管理后台文件上传API端点
仅用于上传文件，不创建内容记录
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import os
import uuid
from datetime import datetime

from ..database import get_db
from ..models import User
from ..utils.auth import require_admin
from ..schemas import FileUploadResponse

router = APIRouter(prefix="/admin/upload", tags=["admin-upload"])


@router.post("/video", response_model=FileUploadResponse)
async def upload_video_file(
    file: UploadFile = File(..., description="视频文件"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    上传视频文件（仅上传，不创建内容记录）
    
    - **file**: 视频文件（MP4、MOV、AVI格式）
    
    返回文件URL
    """
    # 验证文件类型
    allowed_types = ["video/mp4", "video/quicktime", "video/x-msvideo"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_FILE_TYPE",
                "message": "不支持的视频格式，仅支持 MP4、MOV、AVI"
            }
        )
    
    # 验证文件大小（500MB）
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB
    temp_chunks = []
    
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        temp_chunks.append(chunk)
        file_size += len(chunk)
        if file_size > 500 * 1024 * 1024:  # 500MB
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "FILE_TOO_LARGE",
                    "message": "视频文件大小不能超过 500MB"
                }
            )
    
    # 生成文件名
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # 按日期组织目录
    date_path = datetime.now().strftime("%Y/%m/%d")
    storage_dir = f"storage/videos/{date_path}"
    os.makedirs(storage_dir, exist_ok=True)
    
    # 保存文件
    file_path = os.path.join(storage_dir, unique_filename)
    with open(file_path, "wb") as f:
        for chunk in temp_chunks:
            f.write(chunk)
    
    # 返回URL（相对路径）
    file_url = f"/storage/videos/{date_path}/{unique_filename}"
    
    return FileUploadResponse(
        url=file_url,
        filename=file.filename,
        size=file_size,
        content_type=file.content_type
    )


@router.post("/image", response_model=FileUploadResponse)
async def upload_image_file(
    file: UploadFile = File(..., description="图片文件"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    上传图片文件（仅上传，不创建内容记录）
    
    - **file**: 图片文件（JPG、PNG格式）
    
    返回文件URL
    """
    # 验证文件类型
    allowed_types = ["image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_FILE_TYPE",
                "message": "不支持的图片格式，仅支持 JPG、PNG"
            }
        )
    
    # 验证文件大小（2MB）
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB
    temp_chunks = []
    
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        temp_chunks.append(chunk)
        file_size += len(chunk)
        if file_size > 2 * 1024 * 1024:  # 2MB
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "FILE_TOO_LARGE",
                    "message": "图片文件大小不能超过 2MB"
                }
            )
    
    # 生成文件名
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # 按日期组织目录
    date_path = datetime.now().strftime("%Y/%m/%d")
    storage_dir = f"storage/images/{date_path}"
    os.makedirs(storage_dir, exist_ok=True)
    
    # 保存文件
    file_path = os.path.join(storage_dir, unique_filename)
    with open(file_path, "wb") as f:
        for chunk in temp_chunks:
            f.write(chunk)
    
    # 返回URL（相对路径）
    file_url = f"/storage/images/{date_path}/{unique_filename}"
    
    return FileUploadResponse(
        url=file_url,
        filename=file.filename,
        size=file_size,
        content_type=file.content_type
    )
