"""
学习分析API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.models import get_db
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics_schemas import (
    LearningAnalyticsResponse,
    LearningHistoryResponse,
    UpdateLearningStatsRequest
)
from app.utils.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/me", response_model=LearningAnalyticsResponse)
async def get_my_learning_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的学习分析数据
    
    需求：33.1-33.4
    """
    service = AnalyticsService(db)
    analytics = await service.get_learning_analytics(current_user.id)
    return analytics


@router.get("/history", response_model=LearningHistoryResponse)
async def get_my_learning_history(
    days: int = Query(30, ge=1, le=365, description="查询最近多少天的记录"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的学习历史记录
    
    需求：33.1-33.4
    """
    service = AnalyticsService(db)
    records = await service.get_learning_history(current_user.id, days)
    return {"records": records}


@router.post("/update", response_model=LearningAnalyticsResponse)
async def update_learning_stats(
    request: UpdateLearningStatsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新学习统计数据
    
    当用户完成观看视频时调用此接口
    
    需求：33.1-33.4
    """
    service = AnalyticsService(db)
    
    try:
        analytics = await service.update_learning_stats(
            user_id=current_user.id,
            content_id=request.content_id,
            watch_time=request.watch_time
        )
        
        # 同时检查并解锁成就
        from app.services.gamification_service import GamificationService
        gamification_service = GamificationService(db)
        await gamification_service.check_and_unlock_achievements(current_user.id)
        
        return await service.get_learning_analytics(current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/users/{user_id}", response_model=LearningAnalyticsResponse)
async def get_user_learning_analytics(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定用户的学习分析数据
    
    需求：33.1-33.4
    """
    service = AnalyticsService(db)
    analytics = await service.get_learning_analytics(user_id)
    return analytics
