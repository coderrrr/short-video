"""
游戏化API端点 - 排行榜和成就
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Optional

from app.models import get_db
from app.services.gamification_service import GamificationService
from app.schemas.gamification_schemas import (
    LeaderboardResponse,
    UserRankResponse,
    UserAchievementsResponse,
    AllAchievementsResponse
)
from app.utils.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    limit: int = Query(100, ge=1, le=500, description="返回的排名数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取排行榜
    
    需求：34.1-34.4
    """
    service = GamificationService(db)
    leaderboard = await service.get_leaderboard(limit=limit)
    
    return {
        "leaderboard": leaderboard,
        "total_count": len(leaderboard)
    }


@router.get("/leaderboard/my-rank", response_model=UserRankResponse)
async def get_my_rank(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的排名信息
    
    需求：34.1-34.4
    """
    service = GamificationService(db)
    rank_info = await service.get_user_rank(current_user.id)
    
    if not rank_info:
        raise HTTPException(status_code=404, detail="用户不在排行榜中")
    
    return rank_info


@router.post("/leaderboard/update")
async def update_leaderboard(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新排行榜（管理员功能）
    
    需求：34.2
    """
    # TODO: 添加管理员权限检查
    
    service = GamificationService(db)
    await service.update_leaderboard()
    
    return {"message": "排行榜更新成功"}


@router.get("/achievements/me", response_model=UserAchievementsResponse)
async def get_my_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的成就列表
    
    需求：34.3-34.4
    """
    service = GamificationService(db)
    achievements = await service.get_user_achievements(current_user.id)
    
    return {
        "achievements": achievements,
        "total_count": len(achievements)
    }


@router.get("/achievements/all", response_model=AllAchievementsResponse)
async def get_all_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有成就定义
    
    需求：34.3-34.4
    """
    service = GamificationService(db)
    achievements = await service.get_all_achievements()
    
    return {"achievements": achievements}


@router.post("/achievements/initialize")
async def initialize_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    初始化成就系统（管理员功能）
    
    需求：34.3
    """
    # TODO: 添加管理员权限检查
    
    service = GamificationService(db)
    await service.initialize_achievements()
    
    return {"message": "成就系统初始化成功"}


@router.post("/achievements/check")
async def check_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    检查并解锁当前用户的成就
    
    需求：34.4
    """
    service = GamificationService(db)
    await service.check_and_unlock_achievements(current_user.id)
    
    return {"message": "成就检查完成"}
