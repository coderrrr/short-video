"""
数据模型
"""
from .base import Base, engine, AsyncSessionLocal, get_db
from .user import User
from .content import Content, ContentStatus
from .tag import Tag
from .content_tag import ContentTag

from .interaction import Interaction, InteractionType
from .comment import Comment
from .share import Share
from .review_record import ReviewRecord
from .follow import Follow
from .user_preference import UserPreference
from .recommendation_cache import RecommendationCache
from .playback_progress import PlaybackProgress
from .video_quality_preference import VideoQualityPreference
from .download import Download
from .report import Report, ReportReason, ReportStatus
from .topic import Topic, topic_contents
from .collection import Collection, collection_contents
from .learning_reminder import LearningReminder
from .learning_analytics import LearningAnalytics, DailyLearningRecord
from .leaderboard import LeaderboardEntry, Achievement, UserAchievement, AchievementType
from .notification import Notification, NotificationType
from .notification_settings import NotificationSettings

__all__ = [
    "Base",
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "User",
    "Content",
    "ContentStatus",
    "Tag",
    "ContentTag",

    "Interaction",
    "InteractionType",
    "Comment",
    "Share",
    "ReviewRecord",
    "Follow",
    "UserPreference",
    "RecommendationCache",
    "PlaybackProgress",
    "VideoQualityPreference",
    "Download",
    "Report",
    "ReportReason",
    "ReportStatus",
    "Topic",
    "topic_contents",
    "Collection",
    "collection_contents",
    "LearningReminder",
    "LearningAnalytics",
    "DailyLearningRecord",
    "LeaderboardEntry",
    "Achievement",
    "UserAchievement",
    "AchievementType",
    "Notification",
    "NotificationType",
    "NotificationSettings",
]
