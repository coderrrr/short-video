"""
推荐服务测试
"""
import pytest
from datetime import datetime, timedelta
from app.services.recommendation_service import RecommendationService


class TestRecommendationService:
    """推荐服务测试类"""
    
    def test_recommendation_service_constants(self):
        """测试推荐服务常量配置"""
        # 验证权重配置
        assert RecommendationService.ROLE_TAG_WEIGHT == 0.3
        assert RecommendationService.TOPIC_TAG_WEIGHT == 0.25
        assert RecommendationService.CONTENT_TYPE_WEIGHT == 0.15
        assert RecommendationService.CREATOR_WEIGHT == 0.15
        assert RecommendationService.RECENCY_WEIGHT == 0.15
        
        # 验证权重总和接近1.0
        total_weight = (
            RecommendationService.ROLE_TAG_WEIGHT +
            RecommendationService.TOPIC_TAG_WEIGHT +
            RecommendationService.CONTENT_TYPE_WEIGHT +
            RecommendationService.CREATOR_WEIGHT +
            RecommendationService.RECENCY_WEIGHT
        )
        assert abs(total_weight - 1.0) < 0.01  # 允许小误差
    
    def test_interaction_weights(self):
        """测试互动权重配置"""
        assert RecommendationService.VIEW_WEIGHT == 1.0
        assert RecommendationService.LIKE_WEIGHT == 2.0
        assert RecommendationService.FAVORITE_WEIGHT == 3.0
        assert RecommendationService.COMMENT_WEIGHT == 2.5
        assert RecommendationService.SHARE_WEIGHT == 3.5
        
        # 验证权重递增关系
        assert RecommendationService.VIEW_WEIGHT < RecommendationService.LIKE_WEIGHT
        assert RecommendationService.LIKE_WEIGHT < RecommendationService.FAVORITE_WEIGHT
        assert RecommendationService.FAVORITE_WEIGHT > RecommendationService.COMMENT_WEIGHT
        assert RecommendationService.SHARE_WEIGHT > RecommendationService.FAVORITE_WEIGHT
    
    def test_cache_configuration(self):
        """测试缓存配置"""
        assert RecommendationService.CACHE_EXPIRY_HOURS == 6
        assert RecommendationService.TIME_DECAY_DAYS == 30


class TestUserPreferenceModel:
    """用户偏好模型测试"""
    
    def test_user_preference_import(self):
        """测试用户偏好模型导入"""
        from app.models.user_preference import UserPreference
        
        assert UserPreference is not None
        assert hasattr(UserPreference, '__tablename__')
        assert UserPreference.__tablename__ == 'user_preferences'
    
    def test_user_preference_fields(self):
        """测试用户偏好模型字段"""
        from app.models.user_preference import UserPreference
        
        # 验证必要字段存在
        assert hasattr(UserPreference, 'id')
        assert hasattr(UserPreference, 'user_id')
        assert hasattr(UserPreference, 'role_tag_weights')
        assert hasattr(UserPreference, 'topic_tag_weights')
        assert hasattr(UserPreference, 'content_type_weights')
        assert hasattr(UserPreference, 'creator_weights')
        assert hasattr(UserPreference, 'total_watch_count')
        assert hasattr(UserPreference, 'total_watch_duration')
        assert hasattr(UserPreference, 'total_like_count')
        assert hasattr(UserPreference, 'total_favorite_count')
        assert hasattr(UserPreference, 'total_comment_count')
        assert hasattr(UserPreference, 'total_share_count')
        assert hasattr(UserPreference, 'created_at')
        assert hasattr(UserPreference, 'updated_at')


class TestRecommendationCacheModel:
    """推荐缓存模型测试"""
    
    def test_recommendation_cache_import(self):
        """测试推荐缓存模型导入"""
        from app.models.recommendation_cache import RecommendationCache
        
        assert RecommendationCache is not None
        assert hasattr(RecommendationCache, '__tablename__')
        assert RecommendationCache.__tablename__ == 'recommendation_caches'
    
    def test_recommendation_cache_fields(self):
        """测试推荐缓存模型字段"""
        from app.models.recommendation_cache import RecommendationCache
        
        # 验证必要字段存在
        assert hasattr(RecommendationCache, 'id')
        assert hasattr(RecommendationCache, 'user_id')
        assert hasattr(RecommendationCache, 'content_ids')
        assert hasattr(RecommendationCache, 'page')
        assert hasattr(RecommendationCache, 'page_size')
        assert hasattr(RecommendationCache, 'expires_at')
        assert hasattr(RecommendationCache, 'created_at')
        assert hasattr(RecommendationCache, 'updated_at')
    
    def test_recommendation_cache_has_is_expired_method(self):
        """测试推荐缓存有过期检查方法"""
        from app.models.recommendation_cache import RecommendationCache
        
        # 验证方法存在
        assert hasattr(RecommendationCache, 'is_expired')
        assert callable(getattr(RecommendationCache, 'is_expired'))


class TestRecommendationAPI:
    """推荐API测试"""
    
    def test_recommendation_endpoints_exist(self):
        """测试推荐API端点存在"""
        from app.api.contents import router
        
        # 获取所有路由
        routes = [route.path for route in router.routes]
        
        # 验证推荐相关端点存在（需要包含前缀）
        assert any("/recommended" in route for route in routes)
        assert any("/track-view" in route for route in routes)
        assert any("/track-interaction" in route for route in routes)
        assert any("/recommendation-cache/invalidate" in route for route in routes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
