"""
分享相关的API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.share_schemas import (
    ShareLinkRequest,
    ShareLinkResponse,
    ShareRecordResponse
)
from app.services.share_service import ShareService
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/shares", tags=["shares"])


@router.post("", response_model=ShareLinkResponse)
async def share_content(
    request: ShareLinkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    分享内容（简化接口，同时生成链接和记录分享）
    
    - **content_id**: 内容ID
    - **platform**: 分享平台（wechat/link，默认wechat）
    
    返回分享链接和内容信息
    """
    share_service = ShareService(db)
    
    try:
        # 生成分享链接
        share_url, content = await share_service.generate_share_link(
            content_id=request.content_id,
            user_id=current_user.id,
            platform=request.platform
        )
        
        # 记录分享行为
        await share_service.track_share(
            content_id=request.content_id,
            user_id=current_user.id,
            platform=request.platform
        )
        
        return ShareLinkResponse(
            share_url=share_url,
            content_id=content.id,
            title=content.title,
            description=content.description,
            cover_url=content.cover_url,
            message="分享成功"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_SHARE",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SHARE_FAILED",
                "message": f"分享失败: {str(e)}"
            }
        )


@router.post("/generate-link", response_model=ShareLinkResponse)
async def generate_share_link(
    request: ShareLinkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    生成分享链接
    
    - **content_id**: 内容ID
    - **platform**: 分享平台（wechat/link，默认wechat）
    
    返回分享链接和内容信息
    
    验收标准：
    - 需求19.1: 当用户点击分享按钮时，平台应显示包括企业消息传递集成的分享选项
    - 需求19.2: 当用户选择企业消息传递时，平台应打开企业消息传递应用，并预填充包含视频链接的消息
    """
    share_service = ShareService(db)
    
    try:
        share_url, content = await share_service.generate_share_link(
            content_id=request.content_id,
            user_id=current_user.id,
            platform=request.platform
        )
        
        return ShareLinkResponse(
            share_url=share_url,
            content_id=content.id,
            title=content.title,
            description=content.description,
            cover_url=content.cover_url,
            message="分享链接生成成功"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_SHARE",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SHARE_LINK_GENERATION_FAILED",
                "message": f"生成分享链接失败: {str(e)}"
            }
        )


@router.post("/track", response_model=ShareRecordResponse)
async def track_share(
    request: ShareLinkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    记录分享行为
    
    - **content_id**: 内容ID
    - **platform**: 分享平台
    
    返回分享记录
    
    验收标准：
    - 需求19.4: 当视频被分享时，平台应增加视频的分享计数
    """
    share_service = ShareService(db)
    
    try:
        share_record = await share_service.track_share(
            content_id=request.content_id,
            user_id=current_user.id,
            platform=request.platform
        )
        
        return ShareRecordResponse.from_orm(share_record)
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_SHARE",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SHARE_TRACKING_FAILED",
                "message": f"记录分享失败: {str(e)}"
            }
        )


@router.get("/content/{content_id}/count")
async def get_share_count(
    content_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取内容的分享次数
    
    - **content_id**: 内容ID
    
    返回分享次数
    """
    share_service = ShareService(db)
    count = await share_service.get_share_count(content_id)
    
    return {
        "content_id": content_id,
        "share_count": count
    }


@router.get("/user/{user_id}")
async def get_user_shares(
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的分享记录
    
    - **user_id**: 用户ID
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量
    
    返回分享记录列表和总数
    """
    share_service = ShareService(db)
    shares, total = await share_service.get_user_shares(
        user_id=user_id,
        page=page,
        page_size=page_size
    )
    
    return {
        "shares": [ShareRecordResponse.from_orm(share) for share in shares],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/content/{content_id}")
async def get_content_shares(
    content_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    获取内容的分享记录
    
    - **content_id**: 内容ID
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量
    
    返回分享记录列表和总数
    """
    share_service = ShareService(db)
    shares, total = await share_service.get_content_shares(
        content_id=content_id,
        page=page,
        page_size=page_size
    )
    
    return {
        "shares": [ShareRecordResponse.from_orm(share) for share in shares],
        "total": total,
        "page": page,
        "page_size": page_size
    }
