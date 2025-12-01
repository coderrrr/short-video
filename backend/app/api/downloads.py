"""
下载相关API端点
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..models import get_db
from ..services.download_service import DownloadService
from ..schemas.download_schemas import (
    DownloadRequest,
    DownloadResponse,
    DownloadListResponse,
    StorageInfoResponse
)
from ..utils.auth import get_current_user
from ..models import User

router = APIRouter(prefix="/downloads", tags=["下载"])


@router.post("/{content_id}", response_model=DownloadResponse)
async def create_download(
    content_id: str,
    download_request: DownloadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建下载任务
    
    - **content_id**: 内容ID
    - **download_request**: 下载请求
    """
    service = DownloadService(db)
    
    try:
        download = await service.create_download(
            user_id=current_user.id,
            content_id=content_id,
            download_request=download_request
        )
        return download
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建下载任务失败: {str(e)}"
        )


@router.get("/", response_model=DownloadListResponse)
async def get_user_downloads(
    status_filter: Optional[str] = Query(None, alias="status", description="下载状态过滤"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的下载列表
    
    - **status**: 下载状态过滤（可选）
    - **limit**: 返回数量限制
    - **offset**: 偏移量
    """
    service = DownloadService(db)
    
    try:
        downloads = await service.get_user_downloads(
            user_id=current_user.id,
            status=status_filter,
            limit=limit,
            offset=offset
        )
        return downloads
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取下载列表失败: {str(e)}"
        )


@router.delete("/{download_id}")
async def delete_download(
    download_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除下载记录
    
    - **download_id**: 下载ID
    """
    service = DownloadService(db)
    
    success = await service.delete_download(
        user_id=current_user.id,
        download_id=download_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="下载记录不存在"
        )
    
    return {"message": "删除成功"}


@router.get("/storage/info", response_model=StorageInfoResponse)
async def get_storage_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取存储空间信息
    """
    service = DownloadService(db)
    
    try:
        storage_info = await service.get_storage_info(user_id=current_user.id)
        return storage_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取存储空间信息失败: {str(e)}"
        )


@router.put("/{download_id}/progress", response_model=DownloadResponse)
async def update_download_progress(
    download_id: str,
    progress: float = Query(..., ge=0, le=100, description="下载进度"),
    status: str = Query("downloading", description="下载状态"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新下载进度（通常由客户端调用）
    
    - **download_id**: 下载ID
    - **progress**: 下载进度（0-100）
    - **status**: 下载状态
    """
    service = DownloadService(db)
    
    try:
        download = await service.update_download_progress(
            download_id=download_id,
            progress=progress,
            status=status
        )
        return download
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新下载进度失败: {str(e)}"
        )
