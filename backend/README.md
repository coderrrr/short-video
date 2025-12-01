# 企业内部短视频平台 - 后端服务

基于 FastAPI 的后端 API 服务。

## 技术栈

- **框架**: FastAPI 0.109.0
- **数据库**: MySQL 8.0 (开发环境使用Docker)
- **ORM**: SQLAlchemy 2.0
- **异步**: aiomysql
- **认证**: JWT (python-jose)
- **AI/LLM**: OpenAI SDK (兼容各种LLM)
- **视频处理**: FFmpeg, OpenCV
- **测试**: pytest, hypothesis

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI应用入口
│   ├── config.py                    # 配置管理（环境变量、数据库连接）
│   ├── database.py                  # 数据库连接和会话管理
│   ├── models/                      # SQLAlchemy数据模型（18个模型）
│   │   ├── base.py                  # 基础模型类
│   │   ├── user.py                  # 用户模型
│   │   ├── content.py               # 内容模型
│   │   ├── tag.py                   # 标签模型
│   │   ├── content_tag.py           # 内容标签关联
│   │   ├── interaction.py           # 互动记录
│   │   ├── comment.py               # 评论
│   │   ├── follow.py                # 关注关系
│   │   ├── review_record.py         # 审核记录
│   │   ├── playback_progress.py     # 播放进度
│   │   ├── notification.py          # 通知
│   │   ├── learning_analytics.py    # 学习分析
│   │   ├── leaderboard.py           # 排行榜
│   │   ├── topic.py                 # 专题
│   │   ├── collection.py            # 合集
│   │   ├── share.py                 # 分享记录
│   │   ├── download.py              # 下载记录
│   │   └── report.py                # 举报记录
│   ├── schemas/                     # Pydantic数据模式（请求/响应）
│   │   ├── user_schemas.py          # 用户相关模式
│   │   ├── content_schemas.py       # 内容相关模式
│   │   ├── comment_schemas.py       # 评论相关模式
│   │   ├── tag_schemas.py           # 标签相关模式
│   │   ├── analytics_schemas.py     # 分析相关模式
│   │   └── ...                      # 其他模式文件
│   ├── api/                         # API路由（15个模块）
│   │   ├── users.py                 # 用户API（登录、资料、关注）
│   │   ├── contents.py              # 内容API（上传、浏览、搜索）
│   │   ├── comments.py              # 评论API
│   │   ├── playback.py              # 播放API
│   │   ├── learning.py              # 学习计划API
│   │   ├── gamification.py          # 游戏化API
│   │   ├── notifications.py         # 通知API
│   │   ├── shares.py                # 分享API
│   │   ├── downloads.py             # 下载API
│   │   ├── reports.py               # 举报API
│   │   ├── reviews.py               # 审核API
│   │   ├── analytics.py             # 分析API
│   │   ├── admin_contents.py        # 管理后台内容API
│   │   ├── admin_tags.py            # 管理后台标签API
│   │   └── admin_analytics.py       # 管理后台分析API
│   ├── services/                    # 业务逻辑层
│   │   ├── content_service.py       # 内容服务（上传、审核、推荐）
│   │   ├── user_service.py          # 用户服务（认证、资料）
│   │   ├── tag_service.py           # 标签服务
│   │   ├── comment_service.py       # 评论服务
│   │   ├── recommendation_service.py # 推荐服务
│   │   ├── learning_service.py      # 学习计划服务
│   │   ├── gamification_service.py  # 游戏化服务
│   │   ├── notification_service.py  # 通知服务
│   │   ├── storage.py               # 存储服务（抽象层）
│   │   ├── storage_local.py         # 本地存储实现
│   │   ├── storage_s3.py            # S3存储实现
│   │   └── video_editor.py          # 视频编辑服务
│   └── utils/                       # 工具函数
│       ├── auth.py                  # JWT认证工具
│       ├── security.py              # 安全工具（密码哈希等）
│       ├── cache.py                 # 缓存工具
│       ├── encryption.py            # 加密工具
│       ├── performance.py           # 性能优化工具
│       ├── query_optimizer.py       # 查询优化工具
│       └── rate_limiter.py          # 速率限制工具
├── tests/                           # 测试文件
│   ├── conftest.py                  # pytest配置和fixtures
│   ├── test_main.py                 # 主应用测试
│   ├── test_models.py               # 数据模型测试
│   ├── test_content_service.py      # 内容服务测试
│   ├── test_user_service.py         # 用户服务测试
│   ├── test_recommendation_service.py # 推荐服务测试
│   ├── test_admin_tags.py           # 管理后台标签测试
│   ├── test_admin_analytics.py      # 管理后台分析测试
│   ├── test_storage.py              # 存储服务测试
│   ├── test_integration_api.py      # API集成测试
│   ├── test_properties_content.py   # 内容属性测试（PBT）
│   ├── test_properties_workflow.py  # 工作流属性测试（PBT）
│   ├── test_properties_search.py    # 搜索属性测试（PBT）
│   └── test_properties_interactions.py # 互动属性测试（PBT）
├── storage/                         # 本地文件存储（开发环境）
│   ├── videos/                      # 视频文件
│   ├── covers/                      # 封面图片
│   ├── avatars/                     # 用户头像
│   └── temp/                        # 临时文件
├── requirements.txt                 # Python依赖
├── pytest.ini                       # pytest配置
├── Dockerfile                       # Docker镜像构建
├── healthcheck.py                   # 健康检查脚本
├── SECURITY.md                      # 安全配置文档
└── README.md                        # 本文件
```

### 代码架构说明

#### 分层架构

```
API层 (api/) 
    ↓ 调用
业务逻辑层 (services/)
    ↓ 调用
数据访问层 (models/)
    ↓ 访问
数据库 (MySQL)
```

#### 关键设计模式

1. **存储抽象层**: `storage.py` 定义接口，`storage_local.py` 和 `storage_s3.py` 实现，通过配置切换
2. **依赖注入**: 使用FastAPI的依赖注入系统管理数据库会话和服务实例
3. **Repository模式**: 数据访问逻辑封装在service层
4. **DTO模式**: 使用Pydantic schemas作为数据传输对象

#### 数据模型关系

```
User (用户)
  ├── 1:N → Content (创作的内容)
  ├── 1:N → Interaction (互动记录)
  ├── 1:N → Comment (评论)
  ├── N:M → Follow (关注关系)
  └── 1:N → ReviewRecord (审核记录)

Content (内容)
  ├── N:1 → User (创作者)
  ├── N:M → Tag (标签，通过ContentTag)
  ├── 1:N → Interaction (互动记录)
  ├── 1:N → Comment (评论)
  ├── 1:N → ReviewRecord (审核记录)
  └── 1:N → PlaybackProgress (播放进度)

Tag (标签)
  ├── N:M → Content (内容，通过ContentTag)
  └── 1:N → Tag (子标签，自关联)
```

## 环境设置

### 1. 创建Conda环境

```bash
conda create -n short-video python=3.12
conda activate short-video
```

### 2. 安装依赖

```bash
conda run -n short-video pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 到 `.env` 并填入实际配置：

```bash
cp ../.env.example ../.env
```

### 4. 启动MySQL数据库

```bash
cd ..
docker-compose up -d mysql
```

### 5. 运行数据库迁移

```bash
# 初始化数据库（首次运行）
docker-compose exec -T mysql mysql -uroot -proot_password < database/create_database.sql
docker-compose exec -T mysql mysql -uroot -proot_password short_video < database/create_tables.sql
```

### 6. 创建初始管理员账号

**方式一：使用默认管理员账号（快速）**

```bash
conda run -n short-video python create_default_admin.py
```

这将创建默认管理员账号：
- 员工ID: `ADMIN001`
- 密码: `admin123`
- ⚠️ 请在首次登录后立即修改密码！

**方式二：自定义管理员账号（交互式）**

```bash
conda run -n short-video python create_admin.py
```

按提示输入管理员信息：
- 员工ID
- 姓名
- 部门
- 岗位
- 密码

## 运行开发服务器

```bash
conda run -n short-video uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000 查看API文档。

## 运行测试

```bash
# 运行所有测试
conda run -n short-video pytest

# 运行测试并生成覆盖率报告
conda run -n short-video pytest --cov=app --cov-report=html

# 运行基于属性的测试
conda run -n short-video pytest tests/ -k "property"
```

## API文档

启动服务器后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发指南

### 添加新的API端点

1. 在 `app/api/` 下创建路由文件
2. 在 `app/schemas/` 下定义请求/响应模式
3. 在 `app/services/` 下实现业务逻辑
4. 在 `app/models/` 下定义数据模型（如需要）
5. 编写单元测试和基于属性的测试

### 代码规范

- 使用中文注释
- 遵循PEP 8代码风格
- 所有公共函数需要类型注解
- 所有API端点需要文档字符串

## 部署

### Docker部署

```bash
docker build -t video-platform-backend .
docker run -p 8000:8000 video-platform-backend
```

### AWS ECS部署

参考项目根目录的部署文档。


### 认证和授权

所有API请求（除了健康检查和文档端点）都需要JWT认证。

#### 获取访问令牌

```bash
# 使用企业员工ID和密码登录
curl -X POST "http://localhost:8000/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "ADMIN001",
    "password": "admin123"
  }'
```

响应示例：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user-uuid",
    "name": "张三",
    "employee_id": "EMP001",
    "is_kol": false
  }
}
```

#### 使用访问令牌

在所有后续请求中添加Authorization头：

```bash
curl -X GET "http://localhost:8000/contents/recommended" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### 权限级别

- **普通用户**: 可以浏览内容、上传视频、互动
- **KOL用户**: 拥有普通用户权限，内容可跳过部分审核流程
- **管理员**: 拥有所有权限，可以审核内容、管理标签、查看分析数据

### 常用API调用示例

#### 1. 内容管理

**上传视频**

```bash
curl -X POST "http://localhost:8000/contents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "video=@/path/to/video.mp4" \
  -F "title=我的第一个视频" \
  -F "description=这是一个测试视频" \
  -F "content_type=工作知识"
```

响应：
```json
{
  "id": "content-uuid",
  "title": "我的第一个视频",
  "status": "draft",
  "video_url": "https://storage.example.com/videos/content-uuid.mp4",
  "created_at": "2025-11-26T10:00:00Z"
}
```

**提交内容审核**

```bash
curl -X POST "http://localhost:8000/contents/{content_id}/submit" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**获取推荐内容**

```bash
curl -X GET "http://localhost:8000/contents/recommended?page=1&size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

响应：
```json
{
  "items": [
    {
      "id": "content-uuid",
      "title": "视频标题",
      "description": "视频描述",
      "cover_url": "https://storage.example.com/covers/xxx.jpg",
      "video_url": "https://storage.example.com/videos/xxx.mp4",
      "duration": 120,
      "creator": {
        "id": "user-uuid",
        "name": "张三",
        "avatar_url": "https://storage.example.com/avatars/xxx.jpg",
        "is_kol": true
      },
      "stats": {
        "view_count": 1000,
        "like_count": 50,
        "comment_count": 10
      },
      "tags": ["Python", "后端开发"],
      "created_at": "2025-11-26T10:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 20
}
```

#### 2. 搜索和筛选

**搜索内容**

```bash
curl -X GET "http://localhost:8000/contents/search?q=Python&page=1&size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**多维筛选**

```bash
curl -X POST "http://localhost:8000/contents/filter" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": ["工作知识"],
    "tags": ["Python", "后端开发"],
    "page": 1,
    "size": 20
  }'
```

#### 3. 用户互动

**点赞内容**

```bash
curl -X POST "http://localhost:8000/contents/{content_id}/like" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**收藏内容**

```bash
curl -X POST "http://localhost:8000/contents/{content_id}/favorite" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**发表评论**

```bash
curl -X POST "http://localhost:8000/contents/{content_id}/comments" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "很棒的视频！@user123",
    "parent_id": null
  }'
```

**关注用户**

```bash
curl -X POST "http://localhost:8000/users/{user_id}/follow" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 4. 个人中心

**获取我的草稿**

```bash
curl -X GET "http://localhost:8000/contents/my-drafts?page=1&size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**获取观看历史**

```bash
curl -X GET "http://localhost:8000/users/me/history?page=1&size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**获取我的收藏**

```bash
curl -X GET "http://localhost:8000/users/me/favorites?page=1&size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 5. 管理后台API

**审核队列**

```bash
curl -X GET "http://localhost:8000/admin/contents/review-queue?page=1&size=20" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**批准内容**

```bash
curl -X POST "http://localhost:8000/admin/contents/{content_id}/approve" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**拒绝内容**

```bash
curl -X POST "http://localhost:8000/admin/contents/{content_id}/reject" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "内容不符合企业文化标准"
  }'
```

**创建标签**

```bash
curl -X POST "http://localhost:8000/admin/tags" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python",
    "category": "主题标签",
    "parent_id": null
  }'
```

**内容分析**

```bash
curl -X GET "http://localhost:8000/admin/analytics/content/{content_id}" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

响应：
```json
{
  "content_id": "content-uuid",
  "title": "视频标题",
  "metrics": {
    "view_count": 1000,
    "unique_viewers": 800,
    "completion_count": 600,
    "completion_rate": 0.75,
    "like_count": 50,
    "favorite_count": 30,
    "comment_count": 10,
    "share_count": 5
  },
  "daily_stats": [
    {
      "date": "2025-11-26",
      "views": 100,
      "likes": 5
    }
  ]
}
```

### API错误处理

所有API错误响应遵循统一格式：

```json
{
  "code": "ERROR_CODE",
  "message": "用户友好的错误消息",
  "details": {
    "field": "具体错误信息"
  },
  "timestamp": "2025-11-26T10:00:00Z",
  "request_id": "req_abc123"
}
```

常见错误代码：

- `UNAUTHORIZED`: 未认证或令牌无效
- `FORBIDDEN`: 无权限执行此操作
- `NOT_FOUND`: 资源不存在
- `VALIDATION_ERROR`: 输入验证失败
- `VIDEO_FORMAT_UNSUPPORTED`: 不支持的视频格式
- `FILE_SIZE_EXCEEDED`: 文件大小超限
- `CONTENT_UNDER_REVIEW`: 内容正在审核中，无法编辑
- `INTERNAL_SERVER_ERROR`: 服务器内部错误

### API速率限制

为保护系统资源，API实施以下速率限制：

- **普通用户**: 100请求/分钟
- **KOL用户**: 200请求/分钟
- **管理员**: 500请求/分钟

超过限制时返回429状态码：

```json
{
  "code": "RATE_LIMIT_EXCEEDED",
  "message": "请求过于频繁，请稍后再试",
  "retry_after": 60
}
```
