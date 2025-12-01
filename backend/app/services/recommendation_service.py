"""
推荐服务
实现个性化内容推荐算法
"""
import uuid
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict
import math

from ..models import (
    User, Content, ContentStatus, UserPreference, 
    Interaction, InteractionType, ContentTag, Tag, Follow
)


class RecommendationService:
    """推荐服务类"""
    
    # 权重配置
    ROLE_TAG_WEIGHT = 0.3  # 角色标签权重
    TOPIC_TAG_WEIGHT = 0.25  # 主题标签权重
    CONTENT_TYPE_WEIGHT = 0.15  # 内容类型权重
    CREATOR_WEIGHT = 0.15  # 创作者权重
    RECENCY_WEIGHT = 0.15  # 时效性权重
    
    # 互动权重
    VIEW_WEIGHT = 1.0
    LIKE_WEIGHT = 2.0
    FAVORITE_WEIGHT = 3.0
    COMMENT_WEIGHT = 2.5
    SHARE_WEIGHT = 3.5
    
    # 衰减因子
    TIME_DECAY_DAYS = 30  # 30天衰减周期
    
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_preference(self, user_id: str) -> UserPreference:
        """
        获取或创建用户偏好
        
        Args:
            user_id: 用户ID
            
        Returns:
            UserPreference: 用户偏好对象
        """
        # 查询现有偏好
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        preference = result.scalar_one_or_none()
        
        if preference:
            return preference
        
        # 创建新偏好
        preference = UserPreference(
            id=str(uuid.uuid4()),
            user_id=user_id,
            role_tag_weights={},
            topic_tag_weights={},
            content_type_weights={},
            creator_weights={}
        )
        self.db.add(preference)
        await self.db.commit()
        await self.db.refresh(preference)
        
        return preference
    
    async def update_preference_from_view(
        self, 
        user_id: str, 
        content_id: str,
        watch_duration: float
    ):
        """
        根据观看行为更新用户偏好
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            watch_duration: 观看时长（秒）
        """
        # 获取内容信息
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        if not content:
            return
        
        # 获取用户偏好
        preference = await self.get_or_create_preference(user_id)
        
        # 更新观看统计
        preference.total_watch_count += 1
        preference.total_watch_duration += watch_duration
        
        # 计算观看完成度权重
        completion_rate = min(watch_duration / content.duration, 1.0) if content.duration else 0.5
        weight = self.VIEW_WEIGHT * completion_rate
        
        # 更新内容类型偏好
        if content.content_type:
            await self._update_weight_dict(
                preference.content_type_weights,
                content.content_type,
                weight
            )
        
        # 更新创作者偏好
        await self._update_weight_dict(
            preference.creator_weights,
            content.creator_id,
            weight
        )
        
        # 更新标签偏好
        await self._update_tag_preferences(preference, content_id, weight)
        
        preference.updated_at = datetime.utcnow()
        await self.db.commit()
    
    async def update_preference_from_interaction(
        self,
        user_id: str,
        content_id: str,
        interaction_type: InteractionType
    ):
        """
        根据互动行为更新用户偏好
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            interaction_type: 互动类型
        """
        # 获取内容信息
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        if not content:
            return
        
        # 获取用户偏好
        preference = await self.get_or_create_preference(user_id)
        
        # 根据互动类型确定权重
        weight_map = {
            InteractionType.LIKE: self.LIKE_WEIGHT,
            InteractionType.FAVORITE: self.FAVORITE_WEIGHT,
            InteractionType.COMMENT: self.COMMENT_WEIGHT,
            InteractionType.SHARE: self.SHARE_WEIGHT,
        }
        weight = weight_map.get(interaction_type, 1.0)
        
        # 更新互动统计
        if interaction_type == InteractionType.LIKE:
            preference.total_like_count += 1
        elif interaction_type == InteractionType.FAVORITE:
            preference.total_favorite_count += 1
        elif interaction_type == InteractionType.COMMENT:
            preference.total_comment_count += 1
        elif interaction_type == InteractionType.SHARE:
            preference.total_share_count += 1
        
        # 更新内容类型偏好
        if content.content_type:
            await self._update_weight_dict(
                preference.content_type_weights,
                content.content_type,
                weight
            )
        
        # 更新创作者偏好
        await self._update_weight_dict(
            preference.creator_weights,
            content.creator_id,
            weight
        )
        
        # 更新标签偏好
        await self._update_tag_preferences(preference, content_id, weight)
        
        preference.updated_at = datetime.utcnow()
        await self.db.commit()
    
    async def _update_weight_dict(self, weight_dict: Dict, key: str, weight: float):
        """
        更新权重字典
        
        Args:
            weight_dict: 权重字典
            key: 键
            weight: 权重增量
        """
        if not isinstance(weight_dict, dict):
            weight_dict = {}
        
        current_weight = weight_dict.get(key, 0.0)
        weight_dict[key] = current_weight + weight
    
    async def _update_tag_preferences(
        self,
        preference: UserPreference,
        content_id: str,
        weight: float
    ):
        """
        更新标签偏好
        
        Args:
            preference: 用户偏好对象
            content_id: 内容ID
            weight: 权重
        """
        # 获取内容的标签
        result = await self.db.execute(
            select(ContentTag, Tag)
            .join(Tag, ContentTag.tag_id == Tag.id)
            .where(ContentTag.content_id == content_id)
        )
        content_tags = result.all()
        
        for content_tag, tag in content_tags:
            # 根据标签类别更新不同的偏好
            if tag.category == "角色标签":
                await self._update_weight_dict(
                    preference.role_tag_weights,
                    tag.id,
                    weight
                )
            elif tag.category in ["主题标签", "工作知识", "生活分享", "企业文化"]:
                await self._update_weight_dict(
                    preference.topic_tag_weights,
                    tag.id,
                    weight
                )
    
    async def get_recommended_content(
        self,
        user_id: str,
        page: int = 1,
        size: int = 20,
        exclude_viewed: bool = True
    ) -> List[Content]:
        """
        获取推荐内容
        
        Args:
            user_id: 用户ID
            page: 页码
            size: 每页数量
            exclude_viewed: 是否排除已观看内容
            
        Returns:
            List[Content]: 推荐内容列表
        """
        # 获取用户信息
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return []
        
        # 获取用户偏好
        preference = await self.get_or_create_preference(user_id)
        
        # 获取候选内容（已发布的内容），使用eager loading加载creator
        from sqlalchemy.orm import selectinload
        query = select(Content).options(selectinload(Content.creator)).where(
            Content.status == ContentStatus.PUBLISHED
        )
        
        # 排除已观看内容
        if exclude_viewed:
            viewed_subquery = select(Interaction.content_id).where(
                and_(
                    Interaction.user_id == user_id,
                    Interaction.type == InteractionType.LIKE  # 使用任意类型作为观看标记
                )
            )
            query = query.where(Content.id.notin_(viewed_subquery))
        
        # 获取最近30天的内容（提高时效性）
        recent_date = datetime.utcnow() - timedelta(days=30)
        query = query.where(Content.published_at >= recent_date)
        
        result = await self.db.execute(query)
        candidates = result.scalars().all()
        
        # 计算每个内容的推荐分数
        scored_contents = []
        for content in candidates:
            score = await self._calculate_recommendation_score(
                user, preference, content
            )
            scored_contents.append((content, score))
        
        # 按分数排序
        scored_contents.sort(key=lambda x: x[1], reverse=True)
        
        # 获取所有推荐内容（用于缓存）
        all_recommended = [content for content, score in scored_contents]
        
        # 在第一页的前面插入精选内容
        if page == 1:
            # 获取精选内容（按优先级排序）
            featured_query = select(Content).options(selectinload(Content.creator)).where(
                and_(
                    Content.status == ContentStatus.PUBLISHED,
                    Content.is_featured == 1
                )
            ).order_by(
                desc(Content.featured_priority),
                desc(Content.published_at)
            ).limit(5)  # 最多显示5个精选内容
            
            featured_result = await self.db.execute(featured_query)
            featured_contents = list(featured_result.scalars().all())
            
            # 移除推荐列表中已经存在的精选内容（避免重复）
            featured_ids = {c.id for c in featured_contents}
            all_recommended = [c for c in all_recommended if c.id not in featured_ids]
            
            # 将精选内容插入到推荐列表前面
            all_recommended = featured_contents + all_recommended
        
        # 分页
        start = (page - 1) * size
        end = start + size
        
        return all_recommended[start:end]
    
    async def _calculate_recommendation_score(
        self,
        user: User,
        preference: UserPreference,
        content: Content
    ) -> float:
        """
        计算推荐分数
        
        Args:
            user: 用户对象
            preference: 用户偏好对象
            content: 内容对象
            
        Returns:
            float: 推荐分数
        """
        score = 0.0
        
        # 1. 基于角色的推荐
        role_score = await self._calculate_role_score(user, content)
        score += role_score * self.ROLE_TAG_WEIGHT
        
        # 2. 基于主题标签的推荐
        topic_score = await self._calculate_topic_score(preference, content)
        score += topic_score * self.TOPIC_TAG_WEIGHT
        
        # 3. 基于内容类型的推荐
        content_type_score = self._calculate_content_type_score(preference, content)
        score += content_type_score * self.CONTENT_TYPE_WEIGHT
        
        # 4. 基于创作者的推荐
        creator_score = self._calculate_creator_score(preference, content)
        score += creator_score * self.CREATOR_WEIGHT
        
        # 5. 时效性加权
        recency_score = self._calculate_recency_score(content)
        score += recency_score * self.RECENCY_WEIGHT
        
        # 6. 内容热度加权（点赞、收藏等）
        popularity_score = self._calculate_popularity_score(content)
        score += popularity_score * 0.1  # 较小的权重
        
        return score
    
    async def _calculate_role_score(self, user: User, content: Content) -> float:
        """计算基于角色的分数"""
        # 获取内容的角色标签
        result = await self.db.execute(
            select(Tag)
            .join(ContentTag, ContentTag.tag_id == Tag.id)
            .where(
                and_(
                    ContentTag.content_id == content.id,
                    Tag.category == "角色标签"
                )
            )
        )
        role_tags = result.scalars().all()
        
        # 如果用户岗位匹配内容的角色标签，给予高分
        for tag in role_tags:
            if user.position and user.position in tag.name:
                return 1.0
        
        return 0.5  # 默认分数
    
    async def _calculate_topic_score(
        self,
        preference: UserPreference,
        content: Content
    ) -> float:
        """计算基于主题标签的分数"""
        if not preference.topic_tag_weights:
            return 0.5
        
        # 获取内容的主题标签
        result = await self.db.execute(
            select(ContentTag, Tag)
            .join(Tag, ContentTag.tag_id == Tag.id)
            .where(
                and_(
                    ContentTag.content_id == content.id,
                    or_(
                        Tag.category == "主题标签",
                        Tag.category == "工作知识",
                        Tag.category == "生活分享",
                        Tag.category == "企业文化"
                    )
                )
            )
        )
        content_tags = result.all()
        
        if not content_tags:
            return 0.5
        
        # 计算标签匹配分数
        total_weight = 0.0
        matched_weight = 0.0
        
        for content_tag, tag in content_tags:
            tag_weight = preference.topic_tag_weights.get(tag.id, 0.0)
            matched_weight += tag_weight
            total_weight += max(tag_weight, 1.0)
        
        if total_weight == 0:
            return 0.5
        
        return min(matched_weight / total_weight, 1.0)
    
    def _calculate_content_type_score(
        self,
        preference: UserPreference,
        content: Content
    ) -> float:
        """计算基于内容类型的分数"""
        if not content.content_type or not preference.content_type_weights:
            return 0.5
        
        weight = preference.content_type_weights.get(content.content_type, 0.0)
        max_weight = max(preference.content_type_weights.values()) if preference.content_type_weights else 1.0
        
        if max_weight == 0:
            return 0.5
        
        return min(weight / max_weight, 1.0)
    
    def _calculate_creator_score(
        self,
        preference: UserPreference,
        content: Content
    ) -> float:
        """计算基于创作者的分数"""
        if not preference.creator_weights:
            return 0.5
        
        weight = preference.creator_weights.get(content.creator_id, 0.0)
        max_weight = max(preference.creator_weights.values()) if preference.creator_weights else 1.0
        
        if max_weight == 0:
            return 0.5
        
        return min(weight / max_weight, 1.0)
    
    def _calculate_recency_score(self, content: Content) -> float:
        """计算时效性分数"""
        if not content.published_at:
            return 0.5
        
        days_ago = (datetime.utcnow() - content.published_at).days
        
        # 使用指数衰减
        decay_factor = math.exp(-days_ago / self.TIME_DECAY_DAYS)
        
        return decay_factor
    
    def _calculate_popularity_score(self, content: Content) -> float:
        """计算内容热度分数"""
        # 综合考虑各种互动指标
        total_interactions = (
            content.view_count * 0.1 +
            content.like_count * 0.3 +
            content.favorite_count * 0.3 +
            content.comment_count * 0.2 +
            content.share_count * 0.1
        )
        
        # 使用对数缩放避免热门内容过度占优
        if total_interactions <= 0:
            return 0.0
        
        return min(math.log10(total_interactions + 1) / 3.0, 1.0)
