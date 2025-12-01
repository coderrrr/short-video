"""
评论相关的API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.schemas.comment_schemas import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentListResponse,
    UserBrief
)
from app.services.comment_service import CommentService
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("", response_model=CommentResponse)
async def create_comment(
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    发表评论
    
    - **content_id**: 内容ID
    - **text**: 评论文本（1-1000字符）
    - **parent_id**: 父评论ID（回复评论时使用，可选）
    - **mentioned_users**: @提及的用户ID列表（可选）
    
    返回创建的评论信息
    
    验收标准：
    - 需求18.1: 当用户点击评论按钮时，平台应显示评论输入界面
    - 需求18.2: 当用户提交评论时，平台应存储评论文本、作者和时间戳
    - 需求18.3: 当用户在评论中输入"@"时，平台应显示同事选择器
    - 需求18.4: 当用户提及同事时，平台应通知被提及的用户
    """
    comment_service = CommentService(db)
    
    try:
        comment = await comment_service.create_comment(
            user_id=current_user.id,
            comment_data=comment_data
        )
        
        # 加载用户信息
        await db.refresh(comment, ['user'])
        
        # 构建响应
        response = CommentResponse(
            id=comment.id,
            content_id=comment.content_id,
            user_id=comment.user_id,
            user=UserBrief.from_orm(comment.user) if comment.user else None,
            text=comment.text,
            parent_id=comment.parent_id,
            mentioned_users=comment.mentioned_users,
            reply_count=0,
            created_at=comment.created_at
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_COMMENT",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "COMMENT_CREATE_FAILED",
                "message": f"创建评论失败: {str(e)}"
            }
        )


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取评论详情
    
    - **comment_id**: 评论ID
    
    返回评论详细信息
    """
    comment_service = CommentService(db)
    comment = await comment_service.get_comment(comment_id)
    
    if not comment:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "COMMENT_NOT_FOUND",
                "message": "评论不存在"
            }
        )
    
    # 获取回复数量
    reply_count = await comment_service.get_reply_count(comment_id)
    
    response = CommentResponse(
        id=comment.id,
        content_id=comment.content_id,
        user_id=comment.user_id,
        user=UserBrief.from_orm(comment.user) if comment.user else None,
        text=comment.text,
        parent_id=comment.parent_id,
        mentioned_users=comment.mentioned_users,
        reply_count=reply_count,
        created_at=comment.created_at
    )
    
    return response


@router.get("/content/{content_id}", response_model=CommentListResponse)
async def list_content_comments(
    content_id: str,
    page: int = 1,
    page_size: int = 20,
    parent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    查询内容的评论列表
    
    - **content_id**: 内容ID
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量
    - **parent_id**: 父评论ID（如果为None，则查询顶级评论；如果指定，则查询回复）
    
    返回评论列表和总数
    
    验收标准：
    - 需求18.5: 当用户查看评论时，平台应按时间顺序显示它们及作者信息
    """
    comment_service = CommentService(db)
    comments, total = await comment_service.list_comments(
        content_id=content_id,
        page=page,
        page_size=page_size,
        parent_id=parent_id
    )
    
    # 构建响应
    comment_responses = []
    for comment in comments:
        reply_count = await comment_service.get_reply_count(comment.id)
        comment_responses.append(
            CommentResponse(
                id=comment.id,
                content_id=comment.content_id,
                user_id=comment.user_id,
                user=UserBrief.from_orm(comment.user) if comment.user else None,
                text=comment.text,
                parent_id=comment.parent_id,
                mentioned_users=comment.mentioned_users,
                reply_count=reply_count,
                created_at=comment.created_at
            )
        )
    
    return CommentListResponse(
        comments=comment_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/user/{user_id}", response_model=CommentListResponse)
async def list_user_comments(
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的评论列表
    
    - **user_id**: 用户ID
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量
    
    返回评论列表和总数
    """
    comment_service = CommentService(db)
    comments, total = await comment_service.get_user_comments(
        user_id=user_id,
        page=page,
        page_size=page_size
    )
    
    # 构建响应
    comment_responses = []
    for comment in comments:
        reply_count = await comment_service.get_reply_count(comment.id)
        comment_responses.append(
            CommentResponse(
                id=comment.id,
                content_id=comment.content_id,
                user_id=comment.user_id,
                user=UserBrief.from_orm(comment.user) if comment.user else None,
                text=comment.text,
                parent_id=comment.parent_id,
                mentioned_users=comment.mentioned_users,
                reply_count=reply_count,
                created_at=comment.created_at
            )
        )
    
    return CommentListResponse(
        comments=comment_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    comment_data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新评论
    
    - **comment_id**: 评论ID
    - **text**: 更新的评论文本
    
    返回更新后的评论信息
    
    注意：只有评论作者可以编辑评论
    """
    comment_service = CommentService(db)
    
    try:
        comment = await comment_service.update_comment(
            comment_id=comment_id,
            user_id=current_user.id,
            comment_data=comment_data
        )
        
        # 加载用户信息
        await db.refresh(comment, ['user'])
        
        # 获取回复数量
        reply_count = await comment_service.get_reply_count(comment_id)
        
        response = CommentResponse(
            id=comment.id,
            content_id=comment.content_id,
            user_id=comment.user_id,
            user=UserBrief.from_orm(comment.user) if comment.user else None,
            text=comment.text,
            parent_id=comment.parent_id,
            mentioned_users=comment.mentioned_users,
            reply_count=reply_count,
            created_at=comment.created_at
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_COMMENT",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "COMMENT_UPDATE_FAILED",
                "message": f"更新评论失败: {str(e)}"
            }
        )


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除评论
    
    - **comment_id**: 评论ID
    
    返回删除结果
    
    注意：只有评论作者或管理员可以删除评论
    """
    comment_service = CommentService(db)
    
    try:
        # TODO: 检查是否为管理员
        is_admin = False
        
        success = await comment_service.delete_comment(
            comment_id=comment_id,
            user_id=current_user.id,
            is_admin=is_admin
        )
        
        return {
            "success": success,
            "message": "评论删除成功"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_COMMENT",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "COMMENT_DELETE_FAILED",
                "message": f"删除评论失败: {str(e)}"
            }
        )
