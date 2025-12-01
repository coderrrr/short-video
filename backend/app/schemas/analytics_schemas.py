"""
学习分析相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import date


class LearningAnalyticsResponse(BaseModel):
    """学习分析响应"""
    total_videos_watched: int = Field(..., description="总观看视频数")
    total_watch_time: int = Field(..., description="总观看时间（秒）")
    learning_streak_days: int = Field(..., description="学习连续天数")
    last_learning_date: Optional[str] = Field(None, description="最后学习日期")
    category_breakdown: Dict[str, int] = Field(..., description="按分类统计")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_videos_watched": 50,
                "total_watch_time": 18000,
                "learning_streak_days": 7,
                "last_learning_date": "2025-01-15",
                "category_breakdown": {
                    "工作知识": 30,
                    "生活分享": 15,
                    "企业文化": 5
                }
            }
        }


class DailyLearningRecordResponse(BaseModel):
    """每日学习记录响应"""
    date: str = Field(..., description="日期")
    videos_watched: int = Field(..., description="观看视频数")
    watch_time: int = Field(..., description="观看时间（秒）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-01-15",
                "videos_watched": 5,
                "watch_time": 1800
            }
        }


class LearningHistoryResponse(BaseModel):
    """学习历史响应"""
    records: List[DailyLearningRecordResponse] = Field(..., description="每日学习记录列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "records": [
                    {
                        "date": "2025-01-15",
                        "videos_watched": 5,
                        "watch_time": 1800
                    },
                    {
                        "date": "2025-01-14",
                        "videos_watched": 3,
                        "watch_time": 1200
                    }
                ]
            }
        }


class UpdateLearningStatsRequest(BaseModel):
    """更新学习统计请求"""
    content_id: str = Field(..., description="内容ID")
    watch_time: int = Field(..., description="观看时间（秒）", ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "content_id": "550e8400-e29b-41d4-a716-446655440000",
                "watch_time": 300
            }
        }
