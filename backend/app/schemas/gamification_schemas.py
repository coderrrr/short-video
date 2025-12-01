"""
游戏化相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class LeaderboardEntryResponse(BaseModel):
    """排行榜条目响应"""
    rank: int = Field(..., description="排名")
    user_id: str = Field(..., description="用户ID")
    user_name: str = Field(..., description="用户姓名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    department: Optional[str] = Field(None, description="部门")
    is_kol: bool = Field(..., description="是否为KOL")
    score: int = Field(..., description="综合得分")
    videos_watched: int = Field(..., description="观看视频数")
    watch_time: int = Field(..., description="观看时间（秒）")
    videos_created: int = Field(..., description="创作视频数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_name": "张三",
                "avatar_url": "https://example.com/avatar.jpg",
                "department": "技术部",
                "is_kol": True,
                "score": 5000,
                "videos_watched": 100,
                "watch_time": 36000,
                "videos_created": 20
            }
        }


class LeaderboardResponse(BaseModel):
    """排行榜响应"""
    leaderboard: List[LeaderboardEntryResponse] = Field(..., description="排行榜列表")
    total_count: int = Field(..., description="总人数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "leaderboard": [
                    {
                        "rank": 1,
                        "user_id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_name": "张三",
                        "avatar_url": "https://example.com/avatar.jpg",
                        "department": "技术部",
                        "is_kol": True,
                        "score": 5000,
                        "videos_watched": 100,
                        "watch_time": 36000,
                        "videos_created": 20
                    }
                ],
                "total_count": 100
            }
        }


class UserRankResponse(BaseModel):
    """用户排名响应"""
    rank: int = Field(..., description="排名")
    user_id: str = Field(..., description="用户ID")
    user_name: str = Field(..., description="用户姓名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    score: int = Field(..., description="综合得分")
    videos_watched: int = Field(..., description="观看视频数")
    watch_time: int = Field(..., description="观看时间（秒）")
    videos_created: int = Field(..., description="创作视频数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rank": 10,
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_name": "张三",
                "avatar_url": "https://example.com/avatar.jpg",
                "score": 3000,
                "videos_watched": 50,
                "watch_time": 18000,
                "videos_created": 10
            }
        }


class AchievementResponse(BaseModel):
    """成就响应"""
    id: str = Field(..., description="成就ID")
    name: str = Field(..., description="成就名称")
    description: str = Field(..., description="成就描述")
    icon_url: Optional[str] = Field(None, description="成就图标URL")
    achievement_type: str = Field(..., description="成就类型")
    unlocked_at: Optional[str] = Field(None, description="解锁时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "学习达人",
                "description": "观看50个视频",
                "icon_url": "https://example.com/badge.png",
                "achievement_type": "learning_milestone",
                "unlocked_at": "2025-01-15T10:30:00"
            }
        }


class UserAchievementsResponse(BaseModel):
    """用户成就列表响应"""
    achievements: List[AchievementResponse] = Field(..., description="成就列表")
    total_count: int = Field(..., description="总成就数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "achievements": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "学习达人",
                        "description": "观看50个视频",
                        "icon_url": "https://example.com/badge.png",
                        "achievement_type": "learning_milestone",
                        "unlocked_at": "2025-01-15T10:30:00"
                    }
                ],
                "total_count": 1
            }
        }


class AllAchievementsResponse(BaseModel):
    """所有成就定义响应"""
    achievements: List[dict] = Field(..., description="所有成就列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "achievements": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "初学者",
                        "description": "观看10个视频",
                        "icon_url": None,
                        "achievement_type": "learning_milestone",
                        "requirement_value": 10,
                        "requirement_description": "观看10个视频"
                    }
                ]
            }
        }
