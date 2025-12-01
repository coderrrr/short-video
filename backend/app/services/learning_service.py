"""
学习计划服务
"""
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models import (
    Topic, Collection, Content, User, 
    topic_contents, collection_contents,
    Interaction, InteractionType, PlaybackProgress,
    LearningReminder
)
from app.schemas.learning_schemas import (
    TopicCreate, TopicUpdate, CollectionCreate, CollectionUpdate,
    TopicContentAssociation, CollectionContentAssociation,
    ReminderCreate, ReminderUpdate
)


class LearningService:
    """学习计划服务类"""
    
    def __init__(self, db):
        self.db = db
    
    # ============ 专题管理 ============
    
    async def create_topic(
        self, 
        topic_data: TopicCreate, 
        creator_id: str
    ) -> Topic:
        """创建专题"""
        topic = Topic(
            id=str(uuid.uuid4()),
            name=topic_data.name,
            description=topic_data.description,
            cover_url=topic_data.cover_url,
            creator_id=creator_id,
            content_count=len(topic_data.content_ids)
        )
        
        self.db.add(topic)
        await self.db.flush()
        
        # 添加内容关联
        if topic_data.content_ids:
            for idx, content_id in enumerate(topic_data.content_ids):
                stmt = topic_contents.insert().values(
                    topic_id=topic.id,
                    content_id=content_id,
                    order=idx,
                    created_at=datetime.utcnow()
                )
                await self.db.execute(stmt)
        
        await self.db.commit()
        await self.db.refresh(topic)
        return topic
    
    async def get_topic(self, topic_id: str) -> Optional[Topic]:
        """获取专题详情"""
        stmt = select(Topic).where(Topic.id == topic_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_topic_with_contents(self, topic_id: str) -> Optional[Topic]:
        """获取专题及其内容"""
        stmt = (
            select(Topic)
            .options(selectinload(Topic.contents))
            .where(Topic.id == topic_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_topics(
        self, 
        skip: int = 0, 
        limit: int = 20,
        is_active: Optional[bool] = None
    ) -> List[Topic]:
        """获取专题列表"""
        stmt = select(Topic)
        
        if is_active is not None:
            stmt = stmt.where(Topic.is_active == (1 if is_active else 0))
        
        stmt = stmt.order_by(Topic.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def update_topic(
        self, 
        topic_id: str, 
        topic_data: TopicUpdate
    ) -> Optional[Topic]:
        """更新专题"""
        topic = await self.get_topic(topic_id)
        if not topic:
            return None
        
        update_data = topic_data.model_dump(exclude_unset=True)
        
        # 处理is_active字段
        if 'is_active' in update_data:
            update_data['is_active'] = 1 if update_data['is_active'] else 0
        
        for key, value in update_data.items():
            setattr(topic, key, value)
        
        topic.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(topic)
        return topic
    
    async def delete_topic(self, topic_id: str) -> bool:
        """删除专题"""
        topic = await self.get_topic(topic_id)
        if not topic:
            return False
        
        await self.db.delete(topic)
        await self.db.commit()
        return True
    
    async def add_contents_to_topic(
        self, 
        topic_id: str, 
        content_ids: List[str]
    ) -> bool:
        """向专题添加内容"""
        topic = await self.get_topic(topic_id)
        if not topic:
            return False
        
        # 获取当前最大order值
        stmt = select(func.max(topic_contents.c.order)).where(
            topic_contents.c.topic_id == topic_id
        )
        result = await self.db.execute(stmt)
        max_order = result.scalar() or -1
        
        # 添加新内容
        for idx, content_id in enumerate(content_ids):
            stmt = topic_contents.insert().values(
                topic_id=topic_id,
                content_id=content_id,
                order=max_order + idx + 1,
                created_at=datetime.utcnow()
            )
            await self.db.execute(stmt)
        
        # 更新内容计数
        topic.content_count += len(content_ids)
        await self.db.commit()
        return True
    
    async def remove_content_from_topic(
        self, 
        topic_id: str, 
        content_id: str
    ) -> bool:
        """从专题移除内容"""
        stmt = delete(topic_contents).where(
            and_(
                topic_contents.c.topic_id == topic_id,
                topic_contents.c.content_id == content_id
            )
        )
        result = await self.db.execute(stmt)
        
        if result.rowcount > 0:
            # 更新内容计数
            topic = await self.get_topic(topic_id)
            if topic:
                topic.content_count = max(0, topic.content_count - 1)
                await self.db.commit()
            return True
        return False
    
    async def reorder_topic_contents(
        self, 
        topic_id: str, 
        content_orders: List[TopicContentAssociation]
    ) -> bool:
        """重新排序专题内容"""
        topic = await self.get_topic(topic_id)
        if not topic:
            return False
        
        # 更新每个内容的顺序
        for item in content_orders:
            stmt = (
                topic_contents.update()
                .where(
                    and_(
                        topic_contents.c.topic_id == topic_id,
                        topic_contents.c.content_id == item.content_id
                    )
                )
                .values(order=item.order)
            )
            await self.db.execute(stmt)
        
        await self.db.commit()
        return True
    
    # ============ 合集管理 ============
    
    async def create_collection(
        self, 
        collection_data: CollectionCreate, 
        creator_id: str
    ) -> Collection:
        """创建合集"""
        collection = Collection(
            id=str(uuid.uuid4()),
            name=collection_data.name,
            description=collection_data.description,
            cover_url=collection_data.cover_url,
            creator_id=creator_id,
            content_count=len(collection_data.content_orders)
        )
        
        self.db.add(collection)
        await self.db.flush()
        
        # 添加内容关联（按顺序）
        if collection_data.content_orders:
            for item in collection_data.content_orders:
                stmt = collection_contents.insert().values(
                    collection_id=collection.id,
                    content_id=item.content_id,
                    order=item.order,
                    created_at=datetime.utcnow()
                )
                await self.db.execute(stmt)
        
        await self.db.commit()
        await self.db.refresh(collection)
        return collection
    
    async def get_collection(self, collection_id: str) -> Optional[Collection]:
        """获取合集详情"""
        stmt = select(Collection).where(Collection.id == collection_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_collection_with_contents(
        self, 
        collection_id: str
    ) -> Optional[Collection]:
        """获取合集及其内容（按顺序）"""
        stmt = (
            select(Collection)
            .options(selectinload(Collection.contents))
            .where(Collection.id == collection_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_collections(
        self, 
        skip: int = 0, 
        limit: int = 20,
        is_active: Optional[bool] = None
    ) -> List[Collection]:
        """获取合集列表"""
        stmt = select(Collection)
        
        if is_active is not None:
            stmt = stmt.where(Collection.is_active == (1 if is_active else 0))
        
        stmt = stmt.order_by(Collection.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def update_collection(
        self, 
        collection_id: str, 
        collection_data: CollectionUpdate
    ) -> Optional[Collection]:
        """更新合集"""
        collection = await self.get_collection(collection_id)
        if not collection:
            return None
        
        update_data = collection_data.model_dump(exclude_unset=True)
        
        # 处理is_active字段
        if 'is_active' in update_data:
            update_data['is_active'] = 1 if update_data['is_active'] else 0
        
        for key, value in update_data.items():
            setattr(collection, key, value)
        
        collection.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(collection)
        return collection
    
    async def delete_collection(self, collection_id: str) -> bool:
        """删除合集"""
        collection = await self.get_collection(collection_id)
        if not collection:
            return False
        
        await self.db.delete(collection)
        await self.db.commit()
        return True
    
    async def add_contents_to_collection(
        self, 
        collection_id: str, 
        content_orders: List[CollectionContentAssociation]
    ) -> bool:
        """向合集添加内容"""
        collection = await self.get_collection(collection_id)
        if not collection:
            return False
        
        # 添加新内容
        for item in content_orders:
            stmt = collection_contents.insert().values(
                collection_id=collection_id,
                content_id=item.content_id,
                order=item.order,
                created_at=datetime.utcnow()
            )
            await self.db.execute(stmt)
        
        # 更新内容计数
        collection.content_count += len(content_orders)
        await self.db.commit()
        return True
    
    async def remove_content_from_collection(
        self, 
        collection_id: str, 
        content_id: str
    ) -> bool:
        """从合集移除内容"""
        stmt = delete(collection_contents).where(
            and_(
                collection_contents.c.collection_id == collection_id,
                collection_contents.c.content_id == content_id
            )
        )
        result = await self.db.execute(stmt)
        
        if result.rowcount > 0:
            # 更新内容计数
            collection = await self.get_collection(collection_id)
            if collection:
                collection.content_count = max(0, collection.content_count - 1)
                await self.db.commit()
            return True
        return False
    
    async def reorder_collection_contents(
        self, 
        collection_id: str, 
        content_orders: List[CollectionContentAssociation]
    ) -> bool:
        """重新排序合集内容"""
        collection = await self.get_collection(collection_id)
        if not collection:
            return False
        
        # 更新每个内容的顺序
        for item in content_orders:
            stmt = (
                collection_contents.update()
                .where(
                    and_(
                        collection_contents.c.collection_id == collection_id,
                        collection_contents.c.content_id == item.content_id
                    )
                )
                .values(order=item.order)
            )
            await self.db.execute(stmt)
        
        await self.db.commit()
        return True
    
    async def get_next_content_in_collection(
        self, 
        collection_id: str, 
        current_content_id: str
    ) -> Optional[str]:
        """获取合集中的下一个内容ID"""
        # 获取当前内容的order
        stmt = select(collection_contents.c.order).where(
            and_(
                collection_contents.c.collection_id == collection_id,
                collection_contents.c.content_id == current_content_id
            )
        )
        result = await self.db.execute(stmt)
        current_order = result.scalar()
        
        if current_order is None:
            return None
        
        # 获取下一个内容
        stmt = (
            select(collection_contents.c.content_id)
            .where(
                and_(
                    collection_contents.c.collection_id == collection_id,
                    collection_contents.c.order > current_order
                )
            )
            .order_by(collection_contents.c.order)
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar()
    
    # ============ 个性化学习计划 ============
    
    async def generate_learning_plan(
        self, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        生成个性化学习计划
        基于用户的角色、观看历史和互动模式推荐内容
        """
        # 获取用户信息
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return {
                "recommended_topics": [],
                "recommended_collections": [],
                "recommended_contents": []
            }
        
        # 1. 基于角色推荐专题和合集
        # 获取用户已观看的内容标签
        watched_stmt = (
            select(Content.id)
            .join(Interaction, Interaction.content_id == Content.id)
            .where(
                and_(
                    Interaction.user_id == user_id,
                    Interaction.type == InteractionType.VIEW
                )
            )
        )
        watched_result = await self.db.execute(watched_stmt)
        watched_content_ids = [row[0] for row in watched_result.all()]
        
        # 推荐激活的专题（排除用户已完全观看的专题）
        topics_stmt = (
            select(Topic)
            .where(Topic.is_active == 1)
            .order_by(Topic.view_count.desc())
            .limit(5)
        )
        topics_result = await self.db.execute(topics_stmt)
        recommended_topics = list(topics_result.scalars().all())
        
        # 推荐激活的合集（排除用户已完全观看的合集）
        collections_stmt = (
            select(Collection)
            .where(Collection.is_active == 1)
            .order_by(Collection.view_count.desc())
            .limit(5)
        )
        collections_result = await self.db.execute(collections_stmt)
        recommended_collections = list(collections_result.scalars().all())
        
        # 2. 推荐单个内容（基于用户偏好）
        # 获取用户偏好的内容类型
        from app.models import UserPreference
        pref_stmt = select(UserPreference).where(UserPreference.user_id == user_id)
        pref_result = await self.db.execute(pref_stmt)
        user_pref = pref_result.scalar_one_or_none()
        
        contents_stmt = (
            select(Content)
            .where(
                and_(
                    Content.status == "published",
                    Content.id.notin_(watched_content_ids) if watched_content_ids else True
                )
            )
            .order_by(Content.view_count.desc())
            .limit(10)
        )
        
        # 如果有用户偏好，根据偏好过滤
        if user_pref and user_pref.preferred_categories:
            contents_stmt = contents_stmt.where(
                Content.content_type.in_(user_pref.preferred_categories)
            )
        
        contents_result = await self.db.execute(contents_stmt)
        recommended_contents = list(contents_result.scalars().all())
        
        return {
            "user_id": user_id,
            "recommended_topics": recommended_topics,
            "recommended_collections": recommended_collections,
            "recommended_contents": recommended_contents
        }
    
    async def get_learning_plan(
        self, 
        user_id: str
    ) -> Dict[str, Any]:
        """获取用户的学习计划"""
        return await self.generate_learning_plan(user_id)
    
    async def update_plan_progress(
        self, 
        user_id: str, 
        content_id: str,
        completed: bool = True
    ) -> bool:
        """
        更新学习计划进度
        当用户完成一个内容时调用
        """
        # 记录或更新播放进度
        stmt = select(PlaybackProgress).where(
            and_(
                PlaybackProgress.user_id == user_id,
                PlaybackProgress.content_id == content_id
            )
        )
        result = await self.db.execute(stmt)
        progress = result.scalar_one_or_none()
        
        if progress:
            progress.completed = completed
            progress.updated_at = datetime.utcnow()
        else:
            progress = PlaybackProgress(
                id=str(uuid.uuid4()),
                user_id=user_id,
                content_id=content_id,
                completed=completed,
                progress_seconds=0,
                total_seconds=0
            )
            self.db.add(progress)
        
        await self.db.commit()
        return True

    
    # ============ 学习提醒 ============
    
    def _calculate_next_reminder(
        self, 
        frequency: str, 
        time_of_day: str,
        days_of_week: Optional[str] = None
    ) -> datetime:
        """计算下次提醒时间"""
        from datetime import timedelta
        
        now = datetime.utcnow()
        hour, minute = map(int, time_of_day.split(':'))
        
        if frequency == "daily":
            # 每天提醒
            next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_time <= now:
                next_time += timedelta(days=1)
            return next_time
        
        elif frequency == "weekly":
            # 每周提醒（需要days_of_week）
            if not days_of_week:
                # 默认每周一
                days_of_week = "1"
            
            days = [int(d) for d in days_of_week.split(',')]
            current_weekday = now.weekday() + 1  # 1=周一, 7=周日
            
            # 找到下一个提醒日
            next_day = None
            for day in sorted(days):
                if day > current_weekday:
                    next_day = day
                    break
            
            if next_day is None:
                # 下周的第一个提醒日
                next_day = min(days)
                days_ahead = (7 - current_weekday) + next_day
            else:
                days_ahead = next_day - current_weekday
            
            next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_time += timedelta(days=days_ahead)
            
            if next_time <= now:
                next_time += timedelta(days=7)
            
            return next_time
        
        else:
            # custom或其他，默认明天
            next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_time += timedelta(days=1)
            return next_time
    
    async def create_reminder(
        self, 
        user_id: str, 
        reminder_data: ReminderCreate
    ) -> LearningReminder:
        """创建学习提醒"""
        # 检查用户是否已有提醒
        stmt = select(LearningReminder).where(LearningReminder.user_id == user_id)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # 更新现有提醒
            existing.frequency = reminder_data.frequency
            existing.time_of_day = reminder_data.time_of_day
            existing.days_of_week = reminder_data.days_of_week
            existing.enabled = True
            existing.next_reminder_at = self._calculate_next_reminder(
                reminder_data.frequency,
                reminder_data.time_of_day,
                reminder_data.days_of_week
            )
            existing.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        
        # 创建新提醒
        reminder = LearningReminder(
            id=str(uuid.uuid4()),
            user_id=user_id,
            frequency=reminder_data.frequency,
            time_of_day=reminder_data.time_of_day,
            days_of_week=reminder_data.days_of_week,
            enabled=True,
            next_reminder_at=self._calculate_next_reminder(
                reminder_data.frequency,
                reminder_data.time_of_day,
                reminder_data.days_of_week
            )
        )
        
        self.db.add(reminder)
        await self.db.commit()
        await self.db.refresh(reminder)
        return reminder
    
    async def get_reminder(self, user_id: str) -> Optional[LearningReminder]:
        """获取用户的学习提醒设置"""
        stmt = select(LearningReminder).where(LearningReminder.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_reminder(
        self, 
        user_id: str, 
        reminder_data: ReminderUpdate
    ) -> Optional[LearningReminder]:
        """更新学习提醒"""
        reminder = await self.get_reminder(user_id)
        if not reminder:
            return None
        
        update_data = reminder_data.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(reminder, key, value)
        
        # 重新计算下次提醒时间
        if 'frequency' in update_data or 'time_of_day' in update_data or 'days_of_week' in update_data:
            reminder.next_reminder_at = self._calculate_next_reminder(
                reminder.frequency,
                reminder.time_of_day,
                reminder.days_of_week
            )
        
        reminder.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(reminder)
        return reminder
    
    async def disable_reminder(self, user_id: str) -> bool:
        """禁用学习提醒"""
        reminder = await self.get_reminder(user_id)
        if not reminder:
            return False
        
        reminder.enabled = False
        reminder.updated_at = datetime.utcnow()
        await self.db.commit()
        return True
    
    async def get_due_reminders(self) -> List[LearningReminder]:
        """获取需要发送的提醒（用于定时任务）"""
        now = datetime.utcnow()
        stmt = (
            select(LearningReminder)
            .where(
                and_(
                    LearningReminder.enabled == True,
                    LearningReminder.next_reminder_at <= now
                )
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def mark_reminder_sent(self, reminder_id: str) -> bool:
        """标记提醒已发送，并计算下次提醒时间"""
        stmt = select(LearningReminder).where(LearningReminder.id == reminder_id)
        result = await self.db.execute(stmt)
        reminder = result.scalar_one_or_none()
        
        if not reminder:
            return False
        
        # 计算下次提醒时间
        reminder.next_reminder_at = self._calculate_next_reminder(
            reminder.frequency,
            reminder.time_of_day,
            reminder.days_of_week
        )
        reminder.updated_at = datetime.utcnow()
        await self.db.commit()
        return True

    
    # ============ 学习进度跟踪 ============
    
    async def get_learning_progress(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户的学习进度统计
        包括总观看视频数、总完成视频数、总观看时间等
        """
        # 获取总观看视频数（去重）
        watched_stmt = (
            select(func.count(func.distinct(Interaction.content_id)))
            .where(
                and_(
                    Interaction.user_id == user_id,
                    Interaction.type == InteractionType.VIEW
                )
            )
        )
        watched_result = await self.db.execute(watched_stmt)
        total_watched = watched_result.scalar() or 0
        
        # 获取总完成视频数
        completed_stmt = (
            select(func.count(PlaybackProgress.id))
            .where(
                and_(
                    PlaybackProgress.user_id == user_id,
                    PlaybackProgress.completed == True
                )
            )
        )
        completed_result = await self.db.execute(completed_stmt)
        total_completed = completed_result.scalar() or 0
        
        # 获取总观看时间（秒）
        watch_time_stmt = (
            select(func.sum(PlaybackProgress.progress_seconds))
            .where(PlaybackProgress.user_id == user_id)
        )
        watch_time_result = await self.db.execute(watch_time_stmt)
        total_watch_time = watch_time_result.scalar() or 0
        
        # 计算完成百分比
        completion_percentage = 0.0
        if total_watched > 0:
            completion_percentage = (total_completed / total_watched) * 100
        
        return {
            "user_id": user_id,
            "total_watched": total_watched,
            "total_completed": total_completed,
            "total_watch_time": int(total_watch_time),
            "completion_percentage": round(completion_percentage, 2)
        }
    
    async def get_collection_progress(
        self, 
        user_id: str, 
        collection_id: str
    ) -> Dict[str, Any]:
        """获取用户在特定合集的进度"""
        # 获取合集信息
        collection = await self.get_collection(collection_id)
        if not collection:
            return None
        
        # 获取合集中的所有内容ID
        stmt = (
            select(collection_contents.c.content_id)
            .where(collection_contents.c.collection_id == collection_id)
        )
        result = await self.db.execute(stmt)
        content_ids = [row[0] for row in result.all()]
        
        if not content_ids:
            return {
                "collection_id": collection_id,
                "collection_name": collection.name,
                "total_contents": 0,
                "completed_contents": 0,
                "completion_percentage": 0.0
            }
        
        # 获取用户已完成的内容数
        completed_stmt = (
            select(func.count(PlaybackProgress.id))
            .where(
                and_(
                    PlaybackProgress.user_id == user_id,
                    PlaybackProgress.content_id.in_(content_ids),
                    PlaybackProgress.completed == True
                )
            )
        )
        completed_result = await self.db.execute(completed_stmt)
        completed_contents = completed_result.scalar() or 0
        
        total_contents = len(content_ids)
        completion_percentage = (completed_contents / total_contents * 100) if total_contents > 0 else 0.0
        
        return {
            "collection_id": collection_id,
            "collection_name": collection.name,
            "total_contents": total_contents,
            "completed_contents": completed_contents,
            "completion_percentage": round(completion_percentage, 2)
        }
    
    async def get_topic_progress(
        self, 
        user_id: str, 
        topic_id: str
    ) -> Dict[str, Any]:
        """获取用户在特定专题的进度"""
        # 获取专题信息
        topic = await self.get_topic(topic_id)
        if not topic:
            return None
        
        # 获取专题中的所有内容ID
        stmt = (
            select(topic_contents.c.content_id)
            .where(topic_contents.c.topic_id == topic_id)
        )
        result = await self.db.execute(stmt)
        content_ids = [row[0] for row in result.all()]
        
        if not content_ids:
            return {
                "topic_id": topic_id,
                "topic_name": topic.name,
                "total_contents": 0,
                "completed_contents": 0,
                "completion_percentage": 0.0
            }
        
        # 获取用户已完成的内容数
        completed_stmt = (
            select(func.count(PlaybackProgress.id))
            .where(
                and_(
                    PlaybackProgress.user_id == user_id,
                    PlaybackProgress.content_id.in_(content_ids),
                    PlaybackProgress.completed == True
                )
            )
        )
        completed_result = await self.db.execute(completed_stmt)
        completed_contents = completed_result.scalar() or 0
        
        total_contents = len(content_ids)
        completion_percentage = (completed_contents / total_contents * 100) if total_contents > 0 else 0.0
        
        return {
            "topic_id": topic_id,
            "topic_name": topic.name,
            "total_contents": total_contents,
            "completed_contents": completed_contents,
            "completion_percentage": round(completion_percentage, 2)
        }
    
    async def record_progress(
        self, 
        user_id: str, 
        content_id: str,
        progress_seconds: int,
        total_seconds: int,
        completed: bool = False
    ) -> bool:
        """记录学习进度"""
        # 查找现有进度记录
        stmt = select(PlaybackProgress).where(
            and_(
                PlaybackProgress.user_id == user_id,
                PlaybackProgress.content_id == content_id
            )
        )
        result = await self.db.execute(stmt)
        progress = result.scalar_one_or_none()
        
        if progress:
            # 更新现有记录
            progress.progress_seconds = progress_seconds
            progress.total_seconds = total_seconds
            progress.completed = completed
            progress.updated_at = datetime.utcnow()
        else:
            # 创建新记录
            progress = PlaybackProgress(
                id=str(uuid.uuid4()),
                user_id=user_id,
                content_id=content_id,
                progress_seconds=progress_seconds,
                total_seconds=total_seconds,
                completed=completed
            )
            self.db.add(progress)
        
        await self.db.commit()
        return True
    
    async def mark_content_completed(
        self, 
        user_id: str, 
        content_id: str
    ) -> bool:
        """标记内容为已完成"""
        # 获取内容信息以获取总时长
        stmt = select(Content).where(Content.id == content_id)
        result = await self.db.execute(stmt)
        content = result.scalar_one_or_none()
        
        if not content:
            return False
        
        total_seconds = content.duration or 0
        
        return await self.record_progress(
            user_id,
            content_id,
            total_seconds,
            total_seconds,
            completed=True
        )
