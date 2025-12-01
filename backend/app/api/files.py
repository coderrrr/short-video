"""
文件服务API - 提供文件访问接口
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["文件服务"])


@router.get("/{file_path:path}")
async def get_file(file_path: str):
    """
    获取文件
    
    Args:
        file_path: 文件相对路径
    
    Returns:
        文件内容
    """
    # 构建完整文件路径
    storage_path = Path("storage")
    full_path = storage_path / file_path
    
    # 安全检查：确保文件路径在存储目录内
    try:
        full_path = full_path.resolve()
        storage_path = storage_path.resolve()
        
        if not str(full_path).startswith(str(storage_path)):
            raise HTTPException(status_code=403, detail="访问被拒绝")
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not full_path.is_file():
            raise HTTPException(status_code=400, detail="不是有效的文件")
        
        return FileResponse(
            path=str(full_path),
            filename=full_path.name
        )
    
    except Exception as e:
        logger.error(f"获取文件失败: {file_path}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail="获取文件失败")
