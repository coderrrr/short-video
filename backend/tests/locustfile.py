"""
性能测试脚本 - 使用Locust进行负载测试

测试场景：
1. 内容浏览（推荐信息流）- 最频繁的操作
2. 内容搜索 - 常见操作
3. 视频上传 - 资源密集型操作
4. 用户互动（点赞、收藏）- 频繁操作

性能目标：
- API响应时间 < 2s
- 错误率 < 1%
- 支持并发用户数 >= 100
"""

from locust import HttpUser, task, between, events
import random
import json
import time
from typing import Dict, Any


class VideoLearningPlatformUser(HttpUser):
    """模拟企业视频学习平台用户"""
    
    # 用户在请求之间等待1-3秒
    wait_time = between(1, 3)
    
    # 测试数据
    test_user_token = None
    test_content_ids = []
    
    def on_start(self):
        """用户开始测试时的初始化"""
        # 模拟用户登录
        self.login()
        
        # 获取一些测试内容ID
        self.fetch_test_content_ids()
    
    def login(self):
        """模拟用户登录"""
        # 注意：这里需要根据实际的认证机制调整
        # 如果使用JWT，需要获取token
        response = self.client.post(
            "/users/login",
            json={
                "employee_id": f"TEST{random.randint(1000, 9999)}",
                "password": "test_password"
            },
            name="用户登录"
        )
        
        if response.status_code == 200:
            data = response.json()
            self.test_user_token = data.get("access_token")
    
    def fetch_test_content_ids(self):
        """获取一些测试内容ID用于后续操作"""
        response = self.client.get(
            "/contents/recommended",
            params={"page": 1, "size": 20},
            headers=self.get_auth_headers(),
            name="获取推荐内容（初始化）"
        )
        
        if response.status_code == 200:
            data = response.json()
            contents = data.get("items", [])
            self.test_content_ids = [c["id"] for c in contents[:10]]
    
    def get_auth_headers(self) -> Dict[str, str]:
        """获取认证头"""
        if self.test_user_token:
            return {"Authorization": f"Bearer {self.test_user_token}"}
        return {}
    
    @task(10)
    def browse_recommended_content(self):
        """
        浏览推荐内容 - 最频繁的操作
        权重：10（最高）
        """
        page = random.randint(1, 5)
        response = self.client.get(
            "/contents/recommended",
            params={"page": page, "size": 20},
            headers=self.get_auth_headers(),
            name="浏览推荐内容"
        )
        
        # 验证响应时间
        if response.elapsed.total_seconds() > 2:
            events.request.fire(
                request_type="GET",
                name="浏览推荐内容（响应时间超标）",
                response_time=response.elapsed.total_seconds() * 1000,
                response_length=len(response.content),
                exception=Exception(f"响应时间 {response.elapsed.total_seconds():.2f}s 超过2s目标")
            )
    
    @task(5)
    def browse_category_content(self):
        """
        按分类浏览内容
        权重：5
        """
        # 模拟不同的分类
        categories = ["工作知识", "生活分享", "企业文化"]
        category = random.choice(categories)
        
        response = self.client.get(
            "/contents/category",
            params={"category": category, "page": 1, "size": 20},
            headers=self.get_auth_headers(),
            name="按分类浏览内容"
        )
    
    @task(3)
    def search_content(self):
        """
        搜索内容
        权重：3
        """
        # 模拟不同的搜索关键词
        keywords = ["技术", "管理", "培训", "分享", "经验"]
        keyword = random.choice(keywords)
        
        response = self.client.get(
            "/contents/search",
            params={"query": keyword, "page": 1, "size": 20},
            headers=self.get_auth_headers(),
            name="搜索内容"
        )
    
    @task(7)
    def view_content_detail(self):
        """
        查看内容详情
        权重：7
        """
        if not self.test_content_ids:
            return
        
        content_id = random.choice(self.test_content_ids)
        response = self.client.get(
            f"/contents/{content_id}",
            headers=self.get_auth_headers(),
            name="查看内容详情"
        )
    
    @task(4)
    def like_content(self):
        """
        点赞内容
        权重：4
        """
        if not self.test_content_ids:
            return
        
        content_id = random.choice(self.test_content_ids)
        response = self.client.post(
            f"/contents/{content_id}/like",
            headers=self.get_auth_headers(),
            name="点赞内容"
        )
    
    @task(3)
    def favorite_content(self):
        """
        收藏内容
        权重：3
        """
        if not self.test_content_ids:
            return
        
        content_id = random.choice(self.test_content_ids)
        response = self.client.post(
            f"/contents/{content_id}/favorite",
            headers=self.get_auth_headers(),
            name="收藏内容"
        )
    
    @task(2)
    def comment_on_content(self):
        """
        评论内容
        权重：2
        """
        if not self.test_content_ids:
            return
        
        content_id = random.choice(self.test_content_ids)
        comments = [
            "很有帮助！",
            "学到了很多",
            "感谢分享",
            "非常实用",
            "期待更多内容"
        ]
        
        response = self.client.post(
            f"/contents/{content_id}/comments",
            json={"text": random.choice(comments)},
            headers=self.get_auth_headers(),
            name="评论内容"
        )
    
    @task(2)
    def view_user_profile(self):
        """
        查看用户个人资料
        权重：2
        """
        response = self.client.get(
            "/users/me",
            headers=self.get_auth_headers(),
            name="查看个人资料"
        )
    
    @task(2)
    def view_my_favorites(self):
        """
        查看我的收藏
        权重：2
        """
        response = self.client.get(
            "/users/me/favorites",
            params={"page": 1, "size": 20},
            headers=self.get_auth_headers(),
            name="查看我的收藏"
        )
    
    @task(1)
    def view_learning_progress(self):
        """
        查看学习进度
        权重：1
        """
        response = self.client.get(
            "/users/me/learning-progress",
            headers=self.get_auth_headers(),
            name="查看学习进度"
        )


class ContentCreatorUser(HttpUser):
    """模拟内容创作者用户 - 较少但更重的操作"""
    
    wait_time = between(5, 10)
    
    test_user_token = None
    
    def on_start(self):
        """初始化"""
        self.login()
    
    def login(self):
        """登录"""
        response = self.client.post(
            "/users/login",
            json={
                "employee_id": f"CREATOR{random.randint(1000, 9999)}",
                "password": "test_password"
            },
            name="创作者登录"
        )
        
        if response.status_code == 200:
            data = response.json()
            self.test_user_token = data.get("access_token")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """获取认证头"""
        if self.test_user_token:
            return {"Authorization": f"Bearer {self.test_user_token}"}
        return {}
    
    @task(5)
    def view_my_contents(self):
        """
        查看我的发布
        权重：5
        """
        response = self.client.get(
            "/users/me/contents",
            params={"page": 1, "size": 20},
            headers=self.get_auth_headers(),
            name="查看我的发布"
        )
    
    @task(3)
    def view_drafts(self):
        """
        查看草稿
        权重：3
        """
        response = self.client.get(
            "/users/me/drafts",
            params={"page": 1, "size": 20},
            headers=self.get_auth_headers(),
            name="查看草稿"
        )
    
    @task(1)
    def create_draft(self):
        """
        创建草稿（模拟，不实际上传视频）
        权重：1
        """
        draft_data = {
            "title": f"测试视频 {random.randint(1000, 9999)}",
            "description": "这是一个性能测试创建的草稿",
            "content_type": random.choice(["工作知识", "生活分享", "企业文化"]),
            "tags": ["测试", "性能测试"]
        }
        
        response = self.client.post(
            "/contents/drafts",
            json=draft_data,
            headers=self.get_auth_headers(),
            name="创建草稿"
        )


class AdminUser(HttpUser):
    """模拟管理员用户 - 审核和管理操作"""
    
    wait_time = between(10, 20)
    
    test_user_token = None
    
    def on_start(self):
        """初始化"""
        self.login()
    
    def login(self):
        """登录"""
        response = self.client.post(
            "/users/login",
            json={
                "employee_id": "ADMIN001",
                "password": "admin123"
            },
            name="管理员登录"
        )
        
        if response.status_code == 200:
            data = response.json()
            self.test_user_token = data.get("access_token")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """获取认证头"""
        if self.test_user_token:
            return {"Authorization": f"Bearer {self.test_user_token}"}
        return {}
    
    @task(5)
    def view_review_queue(self):
        """
        查看审核队列
        权重：5
        """
        response = self.client.get(
            "/admin/contents/review-queue",
            params={"page": 1, "size": 20},
            headers=self.get_auth_headers(),
            name="查看审核队列"
        )
    
    @task(3)
    def view_content_analytics(self):
        """
        查看内容分析
        权重：3
        """
        response = self.client.get(
            "/admin/analytics/contents",
            params={"page": 1, "size": 20},
            headers=self.get_auth_headers(),
            name="查看内容分析"
        )
    
    @task(2)
    def view_user_interactions(self):
        """
        查看用户互动
        权重：2
        """
        response = self.client.get(
            "/admin/analytics/interactions",
            params={"page": 1, "size": 20},
            headers=self.get_auth_headers(),
            name="查看用户互动"
        )


# 性能测试事件监听器
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时的处理"""
    print("\n" + "="*80)
    print("性能测试开始")
    print("="*80)
    print(f"目标主机: {environment.host}")
    print(f"性能目标: API响应时间 < 2s, 错误率 < 1%")
    print("="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时的处理"""
    print("\n" + "="*80)
    print("性能测试结束")
    print("="*80)
    
    # 获取统计信息
    stats = environment.stats
    
    print(f"\n总请求数: {stats.total.num_requests}")
    print(f"总失败数: {stats.total.num_failures}")
    print(f"失败率: {stats.total.fail_ratio * 100:.2f}%")
    print(f"平均响应时间: {stats.total.avg_response_time:.2f}ms")
    print(f"中位数响应时间: {stats.total.median_response_time:.2f}ms")
    print(f"95%响应时间: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"99%响应时间: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"最大响应时间: {stats.total.max_response_time:.2f}ms")
    print(f"最小响应时间: {stats.total.min_response_time:.2f}ms")
    print(f"RPS (请求/秒): {stats.total.total_rps:.2f}")
    
    # 检查性能目标
    print("\n" + "-"*80)
    print("性能目标检查:")
    print("-"*80)
    
    # 检查响应时间
    avg_response_time_seconds = stats.total.avg_response_time / 1000
    if avg_response_time_seconds < 2:
        print(f"✓ 平均响应时间 {avg_response_time_seconds:.2f}s < 2s 目标")
    else:
        print(f"✗ 平均响应时间 {avg_response_time_seconds:.2f}s >= 2s 目标")
    
    # 检查错误率
    if stats.total.fail_ratio < 0.01:
        print(f"✓ 错误率 {stats.total.fail_ratio * 100:.2f}% < 1% 目标")
    else:
        print(f"✗ 错误率 {stats.total.fail_ratio * 100:.2f}% >= 1% 目标")
    
    print("="*80 + "\n")
