"""
管理后台数据分析服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, distinct
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
from datetime import datetime
import csv
import io

from app.models import (
    Content, User, Interaction, Comment, PlaybackProgress,
    ContentTag, Tag
)
from app.models.content import ContentStatus
from app.models.interaction import InteractionType
from app.schemas.admin_analytics_schemas import (
    ContentPerformanceMetrics,
    ContentAnalyticsSummary,
    ContentDetailedAnalytics,
    InteractionRecord,
    CommentRecord
)


class AdminAnalyticsService:
    """管理后台数据分析服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_content_analytics_summary(self) -> ContentAnalyticsSummary:
        """
        获取内容分析汇总数据
        
        需求：45.1
        """
        # 统计总内容数（已发布）
        total_contents_query = select(func.count(Content.id)).where(
            Content.status == ContentStatus.PUBLISHED
        )
        total_contents_result = await self.db.execute(total_contents_query)
        total_contents = total_contents_result.scalar() or 0
        
        # 统计总观看次数
        total_views_query = select(func.sum(Content.view_count)).where(
            Content.status == ContentStatus.PUBLISHED
        )
        total_views_result = await self.db.execute(total_views_query)
        total_views = total_views_result.scalar() or 0
        
        # 统计总完播次数（观看至少90%）
        total_completions_query = select(func.count(PlaybackProgress.id)).where(
            and_(
                PlaybackProgress.progress_percentage >= 90.0,
                PlaybackProgress.is_completed == 1
            )
        )
        total_completions_result = await self.db.execute(total_completions_query)
        total_completions = total_completions_result.scalar() or 0
        
        # 计算平均完播率
        avg_completion_rate = (total_completions / total_views * 100) if total_views > 0 else 0.0
        
        # 统计总点赞数
        total_likes_query = select(func.sum(Content.like_count)).where(
            Content.status == ContentStatus.PUBLISHED
        )
        total_likes_result = await self.db.execute(total_likes_query)
        total_likes = total_likes_result.scalar() or 0
        
        # 统计总收藏数
        total_favorites_query = select(func.sum(Content.favorite_count)).where(
            Content.status == ContentStatus.PUBLISHED
        )
        total_favorites_result = await self.db.execute(total_favorites_query)
        total_favorites = total_favorites_result.scalar() or 0
        
        # 统计总评论数
        total_comments_query = select(func.sum(Content.comment_count)).where(
            Content.status == ContentStatus.PUBLISHED
        )
        total_comments_result = await self.db.execute(total_comments_query)
        total_comments = total_comments_result.scalar() or 0
        
        # 统计总分享数
        total_shares_query = select(func.sum(Content.share_count)).where(
            Content.status == ContentStatus.PUBLISHED
        )
        total_shares_result = await self.db.execute(total_shares_query)
        total_shares = total_shares_result.scalar() or 0
        
        return ContentAnalyticsSummary(
            total_contents=total_contents,
            total_views=total_views,
            total_completions=total_completions,
            avg_completion_rate=round(avg_completion_rate, 2),
            total_likes=total_likes,
            total_favorites=total_favorites,
            total_comments=total_comments,
            total_shares=total_shares
        )
    
    async def get_content_performance_list(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "view_count",
        order: str = "desc"
    ) -> tuple[List[ContentPerformanceMetrics], int]:
        """
        获取内容性能指标列表
        
        需求：45.1, 45.2
        
        Args:
            page: 页码
            page_size: 每页数量
            sort_by: 排序字段（view_count, completion_rate, like_count等）
            order: 排序方向（asc, desc）
        """
        # 构建基础查询
        query = select(Content).where(
            Content.status == ContentStatus.PUBLISHED
        ).options(
            joinedload(Content.creator)
        )
        
        # 计算每个内容的完播次数和独立观众数
        # 这里我们需要使用子查询
        
        # 获取总数
        count_query = select(func.count(Content.id)).where(
            Content.status == ContentStatus.PUBLISHED
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 排序
        if sort_by == "view_count":
            order_col = Content.view_count
        elif sort_by == "like_count":
            order_col = Content.like_count
        elif sort_by == "favorite_count":
            order_col = Content.favorite_count
        elif sort_by == "comment_count":
            order_col = Content.comment_count
        elif sort_by == "share_count":
            order_col = Content.share_count
        elif sort_by == "published_at":
            order_col = Content.published_at
        else:
            order_col = Content.view_count
        
        if order == "asc":
            query = query.order_by(order_col.asc())
        else:
            query = query.order_by(order_col.desc())
        
        # 分页
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        contents = result.scalars().all()
        
        # 为每个内容计算详细指标
        metrics_list = []
        for content in contents:
            metrics = await self._calculate_content_metrics(content)
            metrics_list.append(metrics)
        
        return metrics_list, total
    
    async def _calculate_content_metrics(self, content: Content) -> ContentPerformanceMetrics:
        """
        计算单个内容的性能指标
        
        需求：45.2, 45.3
        """
        # 计算完播次数（观看至少90%）
        completion_query = select(func.count(PlaybackProgress.id)).where(
            and_(
                PlaybackProgress.content_id == content.id,
                PlaybackProgress.progress_percentage >= 90.0,
                PlaybackProgress.is_completed == 1
            )
        )
        completion_result = await self.db.execute(completion_query)
        completion_count = completion_result.scalar() or 0
        
        # 计算独立观众数
        unique_viewers_query = select(func.count(distinct(PlaybackProgress.user_id))).where(
            PlaybackProgress.content_id == content.id
        )
        unique_viewers_result = await self.db.execute(unique_viewers_query)
        unique_viewers = unique_viewers_result.scalar() or 0
        
        # 计算完播率
        completion_rate = (completion_count / content.view_count * 100) if content.view_count > 0 else 0.0
        
        # 计算平均观看时长
        avg_watch_time_query = select(func.avg(PlaybackProgress.progress_seconds)).where(
            PlaybackProgress.content_id == content.id
        )
        avg_watch_time_result = await self.db.execute(avg_watch_time_query)
        avg_watch_time = avg_watch_time_result.scalar() or 0.0
        
        return ContentPerformanceMetrics(
            content_id=content.id,
            title=content.title,
            creator_name=content.creator.name if content.creator else "未知",
            view_count=content.view_count,
            completion_count=completion_count,
            unique_viewers=unique_viewers,
            like_count=content.like_count,
            favorite_count=content.favorite_count,
            comment_count=content.comment_count,
            share_count=content.share_count,
            completion_rate=round(completion_rate, 2),
            avg_watch_time=round(avg_watch_time, 2),
            published_at=content.published_at
        )
    
    async def get_content_detailed_analytics(self, content_id: str) -> Optional[ContentDetailedAnalytics]:
        """
        获取内容的详细分析数据
        
        需求：45.2
        """
        # 查询内容
        query = select(Content).where(Content.id == content_id).options(
            joinedload(Content.creator),
            joinedload(Content.tags).joinedload(ContentTag.tag)
        )
        result = await self.db.execute(query)
        content = result.scalar_one_or_none()
        
        if not content:
            return None
        
        # 计算完播次数
        completion_query = select(func.count(PlaybackProgress.id)).where(
            and_(
                PlaybackProgress.content_id == content_id,
                PlaybackProgress.progress_percentage >= 90.0,
                PlaybackProgress.is_completed == 1
            )
        )
        completion_result = await self.db.execute(completion_query)
        completion_count = completion_result.scalar() or 0
        
        # 计算独立观众数
        unique_viewers_query = select(func.count(distinct(PlaybackProgress.user_id))).where(
            PlaybackProgress.content_id == content_id
        )
        unique_viewers_result = await self.db.execute(unique_viewers_query)
        unique_viewers = unique_viewers_result.scalar() or 0
        
        # 计算完播率
        completion_rate = (completion_count / content.view_count * 100) if content.view_count > 0 else 0.0
        
        # 计算平均观看时长
        avg_watch_time_query = select(func.avg(PlaybackProgress.progress_seconds)).where(
            PlaybackProgress.content_id == content_id
        )
        avg_watch_time_result = await self.db.execute(avg_watch_time_query)
        avg_watch_time = avg_watch_time_result.scalar() or 0.0
        
        # 计算平均观看百分比
        avg_watch_percentage_query = select(func.avg(PlaybackProgress.progress_percentage)).where(
            PlaybackProgress.content_id == content_id
        )
        avg_watch_percentage_result = await self.db.execute(avg_watch_percentage_query)
        avg_watch_percentage = avg_watch_percentage_result.scalar() or 0.0
        
        # 获取标签
        tags = [ct.tag.name for ct in content.tags if ct.tag]
        
        return ContentDetailedAnalytics(
            content_id=content.id,
            title=content.title,
            description=content.description,
            creator_name=content.creator.name if content.creator else "未知",
            creator_id=content.creator_id,
            duration=content.duration or 0,
            view_count=content.view_count,
            completion_count=completion_count,
            unique_viewers=unique_viewers,
            completion_rate=round(completion_rate, 2),
            avg_watch_time=round(avg_watch_time, 2),
            avg_watch_percentage=round(avg_watch_percentage, 2),
            like_count=content.like_count,
            favorite_count=content.favorite_count,
            comment_count=content.comment_count,
            share_count=content.share_count,
            created_at=content.created_at,
            published_at=content.published_at,
            tags=tags
        )
    
    async def export_analytics_report(
        self,
        content_ids: Optional[List[str]] = None,
        format: str = "csv"
    ) -> bytes:
        """
        导出分析报告
        
        需求：45.4
        
        Args:
            content_ids: 要导出的内容ID列表，为空则导出所有
            format: 导出格式（csv 或 excel）
        
        Returns:
            报告文件的字节数据
        """
        # 查询内容
        query = select(Content).where(
            Content.status == ContentStatus.PUBLISHED
        ).options(
            joinedload(Content.creator)
        )
        
        if content_ids:
            query = query.where(Content.id.in_(content_ids))
        
        result = await self.db.execute(query)
        contents = result.scalars().all()
        
        # 计算每个内容的指标
        metrics_list = []
        for content in contents:
            metrics = await self._calculate_content_metrics(content)
            metrics_list.append(metrics)
        
        # 生成CSV
        if format == "csv":
            return self._generate_csv_report(metrics_list)
        else:
            # Excel格式暂时返回CSV（可以后续扩展）
            return self._generate_csv_report(metrics_list)
    
    def _generate_csv_report(self, metrics_list: List[ContentPerformanceMetrics]) -> bytes:
        """生成CSV报告"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            "内容ID", "标题", "创作者", "观看次数", "完播次数", "独立观众数",
            "点赞数", "收藏数", "评论数", "分享数", "完播率(%)", "平均观看时长(秒)", "发布时间"
        ])
        
        # 写入数据
        for metrics in metrics_list:
            writer.writerow([
                metrics.content_id,
                metrics.title,
                metrics.creator_name,
                metrics.view_count,
                metrics.completion_count,
                metrics.unique_viewers,
                metrics.like_count,
                metrics.favorite_count,
                metrics.comment_count,
                metrics.share_count,
                metrics.completion_rate,
                metrics.avg_watch_time,
                metrics.published_at.strftime("%Y-%m-%d %H:%M:%S") if metrics.published_at else ""
            ])
        
        # 转换为字节
        return output.getvalue().encode('utf-8-sig')  # 使用utf-8-sig以支持Excel打开中文
    
    async def get_interaction_records(
        self,
        interaction_type: str,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[str] = None,
        content_id: Optional[str] = None
    ) -> tuple[List[InteractionRecord], int]:
        """
        获取用户互动记录
        
        需求：49.1, 49.2, 49.3
        
        Args:
            interaction_type: 互动类型（like, favorite, bookmark）
            page: 页码
            page_size: 每页数量
            user_id: 筛选用户ID
            content_id: 筛选内容ID
        """
        # 构建查询
        query = select(Interaction).options(
            joinedload(Interaction.user),
            joinedload(Interaction.content)
        )
        
        # 筛选条件
        conditions = [Interaction.type == interaction_type]
        if user_id:
            conditions.append(Interaction.user_id == user_id)
        if content_id:
            conditions.append(Interaction.content_id == content_id)
        
        query = query.where(and_(*conditions))
        
        # 获取总数
        count_query = select(func.count(Interaction.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 排序和分页
        query = query.order_by(Interaction.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        interactions = result.scalars().all()
        
        # 转换为响应格式
        records = []
        for interaction in interactions:
            records.append(InteractionRecord(
                id=interaction.id,
                user_id=interaction.user_id,
                user_name=interaction.user.name if interaction.user else "未知",
                content_id=interaction.content_id,
                content_title=interaction.content.title if interaction.content else "未知",
                interaction_type=interaction.type,
                note=interaction.note if interaction.type == InteractionType.BOOKMARK else None,
                created_at=interaction.created_at
            ))
        
        return records, total
    
    async def get_comment_records(
        self,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[str] = None,
        content_id: Optional[str] = None,
        search_text: Optional[str] = None
    ) -> tuple[List[CommentRecord], int]:
        """
        获取评论记录
        
        需求：49.4
        
        Args:
            page: 页码
            page_size: 每页数量
            user_id: 筛选用户ID
            content_id: 筛选内容ID
            search_text: 搜索评论文本
        """
        # 构建查询
        query = select(Comment).options(
            joinedload(Comment.user),
            joinedload(Comment.content)
        )
        
        # 筛选条件
        conditions = []
        if user_id:
            conditions.append(Comment.user_id == user_id)
        if content_id:
            conditions.append(Comment.content_id == content_id)
        if search_text:
            conditions.append(Comment.text.contains(search_text))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 获取总数
        count_query = select(func.count(Comment.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 排序和分页
        query = query.order_by(Comment.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        comments = result.scalars().all()
        
        # 转换为响应格式
        records = []
        for comment in comments:
            records.append(CommentRecord(
                id=comment.id,
                user_id=comment.user_id,
                user_name=comment.user.name if comment.user else "未知",
                content_id=comment.content_id,
                content_title=comment.content.title if comment.content else "未知",
                text=comment.text,
                parent_id=comment.parent_id,
                mentioned_users=comment.mentioned_users or [],
                created_at=comment.created_at
            ))
        
        return records, total
    
    async def delete_comment(self, comment_id: str) -> bool:
        """
        删除评论
        
        需求：49.5
        """
        query = select(Comment).where(Comment.id == comment_id)
        result = await self.db.execute(query)
        comment = result.scalar_one_or_none()
        
        if not comment:
            return False
        
        # 删除评论
        await self.db.delete(comment)
        
        # 更新内容的评论计数
        content_query = select(Content).where(Content.id == comment.content_id)
        content_result = await self.db.execute(content_query)
        content = content_result.scalar_one_or_none()
        
        if content and content.comment_count > 0:
            content.comment_count -= 1
        
        await self.db.commit()
        return True
