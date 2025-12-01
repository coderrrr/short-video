# 设计文档

## 概述

企业内部短视频平台是一个自建的移动优先内容共享系统，旨在鼓励员工创作和分享工作知识与美好生活，丰富企业文化。系统采用前后端分离架构，C端以H5方式集成在企业现有App中，管理端提供PC Web界面。

### 核心目标

1. **鼓励员工创作**：提供简单易用的视频制作和上传工具
2. **知识共享**：通过手动标签和推荐，帮助员工发现相关内容
3. **生活分享**：支持员工分享美好生活瞬间，增强团队凝聚力
4. **企业文化建设**：通过人工审核和精选推荐，传播企业价值观
5. **人工管理**：标签由管理员手动分配，内容由人工审核

### 技术约束

- **C端**：H5页面，集成在企业现有App中，无独立PC Web界面
- **管理端**：PC Web应用，响应式设计
- **语言**：所有界面和文档使用中文

## 架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        企业现有App                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              C端 H5 页面                              │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐      │   │
│  │  │视频上传│   │内容浏览│    │互动功能│   │个人中心│       │   │
│  │  └────────┘  └────────┘  └────────┘  └────────┘      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS/REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                            │
│                       (路由、日志)                            │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  内容服务     │   │  用户服务     │   │  标签服务     │
│              │   │              │   │              │
│ - 视频管理    │   │ - 用户管理    │   │ - 手动标签    │
│ - 元数据管理  │   │ - 认证授权    │   │ - 分类管理    │
│ - 审核流程    │   │ - 关注关系    │   │              │
│ - 推荐算法    │   │ - 互动记录    │   │              │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
        ┌──────────────┐       ┌──────────────┐
        │  MySQL       │       │  S3          │
        │  (元数据)     │       │  (视频文件)   │
        │              │       │              │
        │ 开发环境:     │       │ 开发环境:     │
        │ Docker MySQL │       │ 本地存储      │
        └──────────────┘       └──────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    管理端 PC Web                             │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐             │
│  │内容管理 │  │审核管理  │  │标签管理 │  │数据分析 │             │
│  └────────┘  └────────┘  └────────┘  └────────┘             │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈选择

#### C端 (Flutter)
- **框架**: Flutter 3.x
- **UI组件**: Material Design / Cupertino (Flutter内置)
- **视频播放**: video_player / chewie
- **状态管理**: Provider / Riverpod
- **HTTP客户端**: dio
- **路由**: go_router
- **本地存储**: shared_preferences / hive
- **注**: 使用Flutter可以将H5编译为WebView集成，未来也可编译为Native App

#### 管理端 (PC Web)
- **框架**: Vue 3 + Vite
- **UI组件**: Element Plus
- **图表**: ECharts
- **状态管理**: Pinia
- **HTTP客户端**: Axios
- **路由**: Vue Router

#### 后端服务
- **语言**: Python 3.12+
- **框架**: FastAPI
- **ORM**: SQLAlchemy
- **任务队列**: Celery + 数据库后端（开发环境）/ AWS SQS（生产环境）
- **数据库**: 
  - 开发/测试环境：Docker MySQL 8.0
  - 生产环境：AWS RDS MySQL 8.0
- **对象存储**: 
  - 开发/测试环境：本地文件系统
  - 生产环境：AWS S3

#### 视频处理
- **视频处理**: FFmpeg（用于视频编辑功能）

## 组件和接口

### C端核心组件

#### 1. 视频上传组件 (VideoUploader)


**职责**：
- 调用设备相机进行视频录制
- 从相册选择视频文件
- 显示上传进度
- 视频格式验证和大小限制

**接口**：
```dart
class VideoUploader extends StatefulWidget {
  final int maxSize;                    // 最大文件大小（MB）
  final List<String> acceptFormats;     // 接受的视频格式
  final VoidCallback onUploadStart;
  final Function(double progress) onUploadProgress;
  final Function(String videoId) onUploadComplete;
  final Function(Exception error) onUploadError;
  
  const VideoUploader({
    required this.maxSize,
    required this.acceptFormats,
    required this.onUploadStart,
    required this.onUploadProgress,
    required this.onUploadComplete,
    required this.onUploadError,
  });
}
```

#### 2. 视频编辑组件 (VideoEditor)

**职责**：
- 视频裁剪（时间轴选择）
- 音量调节
- 封面选择（视频帧或本地图片）
- 实时预览

**接口**：
```dart
class VideoEditor extends StatefulWidget {
  final String videoUrl;
  final Function(EditedVideoData) onSave;
  final VoidCallback onCancel;
  
  const VideoEditor({
    required this.videoUrl,
    required this.onSave,
    required this.onCancel,
  });
}

class EditedVideoData {
  final double startTime;
  final double endTime;
  final double volume;
  final String coverImage;  // base64 or URL
  
  EditedVideoData({
    required this.startTime,
    required this.endTime,
    required this.volume,
    required this.coverImage,
  });
}
```

#### 3. 视频播放器组件 (VideoPlayer)

**职责**：
- 视频播放控制（播放、暂停、进度）
- 倍速播放
- 手势控制（滑动切换）
- 自动播放下一个

**接口**：
```dart
class VideoPlayer extends StatefulWidget {
  final String videoUrl;
  final bool autoPlay;
  final bool showControls;
  final VoidCallback onPlayEnd;
  final Function(Exception error) onError;
  
  const VideoPlayer({
    required this.videoUrl,
    this.autoPlay = false,
    this.showControls = true,
    required this.onPlayEnd,
    required this.onError,
  });
}
```

#### 4. 内容信息流组件 (ContentFeed)

**职责**：
- 瀑布流/列表展示内容
- 下拉刷新、上拉加载
- 内容预览卡片
- 快速互动按钮

**接口**：
```dart
enum FeedType { recommend, following, category }

class ContentFeed extends StatefulWidget {
  final FeedType feedType;
  final String? categoryId;
  final Future<List<Content>> Function() onLoadMore;
  final Future<List<Content>> Function() onRefresh;
  
  const ContentFeed({
    required this.feedType,
    this.categoryId,
    required this.onLoadMore,
    required this.onRefresh,
  });
}

class Content {
  final String id;
  final String title;
  final String coverUrl;
  final String videoUrl;
  final User creator;
  final ContentStats stats;
  final List<String> tags;
  
  Content({
    required this.id,
    required this.title,
    required this.coverUrl,
    required this.videoUrl,
    required this.creator,
    required this.stats,
    required this.tags,
  });
}
```

### 后端核心服务

#### 1. 内容服务 (ContentService)

**职责**：
- 视频上传和存储
- 元数据管理
- 内容审核流程
- 内容推荐算法

**主要API**：
```python
class ContentService:
    async def upload_video(
        self, 
        file: UploadFile, 
        metadata: VideoMetadata,
        user_id: str
    ) -> str:
        """上传视频并返回视频ID"""
        
    async def submit_for_review(
        self, 
        video_id: str
    ) -> ReviewStatus:
        """提交内容进行审核"""
        
    async def get_recommended_content(
        self, 
        user_id: str,
        page: int,
        size: int
    ) -> List[Content]:
        """获取推荐内容"""
        
    async def search_content(
        self,
        query: str,
        filters: Dict[str, Any],
        page: int,
        size: int
    ) -> SearchResult:
        """搜索内容"""
```

#### 2. 用户服务 (UserService)

**职责**：
- 用户认证和授权
- 用户资料管理
- 关注关系管理
- 互动记录（点赞、收藏、评论）

**主要API**：
```python
class UserService:
    async def authenticate(
        self,
        token: str
    ) -> User:
        """验证用户身份"""
        
    async def follow_user(
        self,
        follower_id: str,
        followee_id: str
    ) -> bool:
        """关注用户"""
        
    async def interact_with_content(
        self,
        user_id: str,
        content_id: str,
        action: InteractionType
    ) -> bool:
        """用户互动（点赞、收藏等）"""
```

## 数据模型

### 核心实体

#### 1. 用户 (User)

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    employee_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    avatar_url = Column(String(500))
    department = Column(String(100))
    position = Column(String(100))
    is_kol = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # 关系
    contents = relationship("Content", back_populates="creator")
    followers = relationship("Follow", foreign_keys="Follow.followee_id")
    following = relationship("Follow", foreign_keys="Follow.follower_id")
```

#### 2. 内容 (Content)

```python
class Content(Base):
    __tablename__ = "contents"
    
    id = Column(String(36), primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    video_url = Column(String(500), nullable=False)
    cover_url = Column(String(500))
    duration = Column(Integer)  # 秒
    file_size = Column(BigInteger)  # 字节
    
    creator_id = Column(String(36), ForeignKey("users.id"))
    status = Column(Enum(ContentStatus))  # draft, under_review, approved, rejected, published, removed
    
    # 内容类型
    content_type = Column(String(50))  # 工作知识、生活分享、企业文化等
    
    # 统计数据
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    
    # 关系
    creator = relationship("User", back_populates="contents")
    tags = relationship("ContentTag", back_populates="content")
```

#### 3. 标签 (Tag)

```python
class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(50), nullable=False)
    category = Column(String(50))  # 角色标签、主题标签、形式标签、质量标签、推荐标签
    parent_id = Column(String(36), ForeignKey("tags.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    children = relationship("Tag")
    contents = relationship("ContentTag", back_populates="tag")
```

#### 4. 内容标签关联 (ContentTag)

```python
class ContentTag(Base):
    __tablename__ = "content_tags"
    
    id = Column(String(36), primary_key=True)
    content_id = Column(String(36), ForeignKey("contents.id"))
    tag_id = Column(String(36), ForeignKey("tags.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    content = relationship("Content", back_populates="tags")
    tag = relationship("Tag", back_populates="contents")
```

#### 5. 互动记录 (Interaction)

```python
class Interaction(Base):
    __tablename__ = "interactions"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"))
    content_id = Column(String(36), ForeignKey("contents.id"))
    type = Column(Enum(InteractionType))  # like, favorite, bookmark, comment, share
    
    # 针对bookmark的额外字段
    note = Column(Text)  # 标记笔记
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_user_content_type', 'user_id', 'content_id', 'type'),
    )
```

#### 6. 评论 (Comment)

```python
class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(String(36), primary_key=True)
    content_id = Column(String(36), ForeignKey("contents.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    text = Column(Text, nullable=False)
    parent_id = Column(String(36), ForeignKey("comments.id"))  # 回复评论
    
    # @提及的用户
    mentioned_users = Column(JSON)  # ["user_id1", "user_id2"]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    replies = relationship("Comment")
```

#### 7. 审核记录 (ReviewRecord)

```python
class ReviewRecord(Base):
    __tablename__ = "review_records"
    
    id = Column(String(36), primary_key=True)
    content_id = Column(String(36), ForeignKey("contents.id"))
    reviewer_id = Column(String(36), ForeignKey("users.id"))
    review_type = Column(String(20))  # platform_review, expert_review, ai_review
    
    status = Column(String(20))  # approved, rejected, pending
    reason = Column(Text)  # 拒绝原因
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 数据库索引策略

```python
# 内容表索引
Index('idx_content_creator', Content.creator_id)
Index('idx_content_status', Content.status)
Index('idx_content_published', Content.published_at.desc())
Index('idx_content_type', Content.content_type)

# 标签关联索引
Index('idx_content_tag_content', ContentTag.content_id)
Index('idx_content_tag_tag', ContentTag.tag_id)

# 互动记录索引
Index('idx_interaction_user', Interaction.user_id)
Index('idx_interaction_content', Interaction.content_id)
Index('idx_interaction_type', Interaction.type)

# 评论索引
Index('idx_comment_content', Comment.content_id)
Index('idx_comment_user', Comment.user_id)
Index('idx_comment_created', Comment.created_at.desc())
```

## 正确性属性

基于需求文档的验收标准，我们定义以下正确性属性：

### 内容上传和管理属性

**属性 1：视频格式验证**
*对于任何*上传的视频文件，如果其格式为MP4、MOV或AVI，则系统应接受该文件；否则应拒绝
**验证需求：1.3**

**属性 2：文件大小限制**
*对于任何*上传的视频文件，如果其大小超过配置的最大限制，则系统应拒绝上传并返回包含最大允许大小的错误消息
**验证需求：1.4**

**属性 2.5：视频自动压缩（仅Native App）**
*对于任何*在Native App环境下上传的视频文件，如果其大小超过压缩阈值（如50MB），则系统应自动压缩视频并记录压缩前后的文件大小（Web环境下跳过压缩）
**验证需求：1.5**

**属性 3：元数据标题必填**
*对于任何*内容保存或提交操作，如果标题字段为空或仅包含空白字符，则系统应拒绝该操作
**验证需求：2.1, 2.5**

**属性 4：描述长度限制**
*对于任何*内容元数据，描述字段的字符数应不超过500个字符
**验证需求：2.2**

**属性 5：草稿往返一致性**
*对于任何*保存为草稿的内容，重新加载该草稿应返回与保存时完全相同的视频和元数据
**验证需求：5.3**

**属性 6：草稿删除完整性**
*对于任何*被删除的草稿，该草稿及其相关文件应从存储中完全移除，后续查询不应返回该草稿
**验证需求：5.4**

### 状态转换属性

**属性 7：内容状态转换正确性**
*对于任何*内容，其状态转换应遵循以下规则：
- 草稿 → 审核中（提交时）
- 审核中 → 已发布（批准时）
- 审核中 → 已驳回（拒绝时）
- 已发布 → 已下架（删除时）
**验证需求：5.1, 6.1, 6.4, 6.5**

**属性 8：审核中内容不可编辑**
*对于任何*状态为"审核中"的内容，创作者的编辑请求应被拒绝
**验证需求：6.3**

### 查询和过滤属性

**属性 16：分类过滤正确性**
*对于任何*分类查询，返回的所有内容应标记有该分类或其子分类，且状态为"已发布"
**验证需求：9.2, 9.4**

**属性 17：草稿列表过滤**
*对于任何*用户的草稿列表查询，返回的所有内容应属于该用户且状态为"草稿"
**验证需求：5.2**

**属性 18：搜索结果相关性**
*对于任何*搜索查询，返回的所有内容的标题、描述或标签应包含至少一个查询关键词
**验证需求：12.1, 12.3**

**属性 19：多筛选器AND逻辑**
*对于任何*应用了多个筛选器的查询，返回的所有内容应满足所有筛选条件
**验证需求：13.2, 13.3**

**属性 20：关注信息流过滤**
*对于任何*用户的关注信息流，返回的所有内容应来自该用户关注的创作者
**验证需求：11.2**

### 互动操作属性

**属性 21：收藏操作幂等性**
*对于任何*用户和内容，多次执行收藏操作应产生与单次操作相同的结果（收藏列表包含该内容）
**验证需求：15.1**

**属性 22：取消收藏正确性**
*对于任何*已收藏的内容，执行取消收藏操作后，该内容不应出现在用户的收藏列表中
**验证需求：15.3**

**属性 23：点赞计数一致性**
*对于任何*内容，其点赞计数应等于点赞该内容的唯一用户数量
**验证需求：17.1, 17.2, 17.4**

**属性 24：关注关系对称性**
*对于任何*用户A和用户B，如果A关注B，则B的关注者列表应包含A，且A的关注列表应包含B
**验证需求：11.1, 11.5**

**属性 25：取消关注清理**
*对于任何*用户取消关注创作者的操作，该创作者的内容不应再出现在用户的关注信息流中
**验证需求：11.4**

**属性 26：级联删除一致性**
*对于任何*被删除的内容，所有相关的收藏、点赞、评论、标记记录应被清理或标记为无效
**验证需求：15.4**

### 推荐算法属性

**属性 27：推荐考虑用户特征**
*对于任何*用户的推荐内容，推荐算法应考虑用户的角色标签、观看历史和互动模式
**验证需求：10.2**

**属性 28：互动更新偏好**
*对于任何*用户与内容的互动（观看、点赞、收藏），系统应更新用户的偏好配置文件
**验证需求：10.3**

**属性 29：新内容推荐评估**
*对于任何*新发布的内容，系统应评估其与用户偏好的匹配度，并决定是否包含在相关用户的推荐信息流中
**验证需求：10.4**

### 通知属性

**属性 30：审核状态通知**
*对于任何*内容状态变更为"审核中"、"已发布"或"已驳回"，系统应向相关人员（审核员或创作者）发送通知
**验证需求：6.2, 6.5**

**属性 31：提及通知**
*对于任何*评论中被@提及的用户，系统应向该用户发送通知
**验证需求：18.4**

**属性 32：互动通知**
*对于任何*用户的内容被点赞、评论或分享，如果该用户启用了互动通知，系统应向该用户发送通知
**验证需求：35.4**

## 错误处理

### 错误分类

#### 1. 客户端错误 (4xx)

**输入验证错误**
- 视频格式不支持
- 文件大小超限
- 必填字段缺失
- 字段长度超限

**权限错误**
- 未认证用户
- 无权限操作（如编辑审核中的内容）
- KOL权限不足

**资源不存在错误**
- 内容不存在
- 用户不存在
- 标签不存在

#### 2. 服务器错误 (5xx)

**存储错误**
- 视频上传失败
- 数据库写入失败
- 数据库连接失败

**第三方服务错误**
- 企业微信集成失败
- AWS S3服务不可用

### 错误处理策略

#### 断路器模式

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def upload_to_s3(file_path: str, object_key: str) -> str:
    """
    上传文件到AWS S3，使用断路器防止级联失败
    """
    return await s3_client.upload_file(file_path, object_key)
```

### 错误响应格式

```typescript
interface ErrorResponse {
  code: string;           // 错误代码
  message: string;        // 用户友好的错误消息（中文）
  details?: any;          // 详细错误信息（可选）
  timestamp: string;      // 错误发生时间
  request_id: string;     // 请求ID，用于追踪
}

// 示例
{
  "code": "VIDEO_FORMAT_UNSUPPORTED",
  "message": "不支持的视频格式，请上传MP4、MOV或AVI格式的视频",
  "details": {
    "uploaded_format": "wmv",
    "supported_formats": ["mp4", "mov", "avi"]
  },
  "timestamp": "2025-01-15T10:30:00Z",
  "request_id": "req_abc123"
}
```

## 测试策略

### 双重测试方法

本系统采用单元测试和基于属性的测试相结合的方法：

- **单元测试**：验证特定示例、边界情况和错误条件
- **基于属性的测试**：验证应在所有输入中保持的通用属性

两者互补，共同提供全面的覆盖：单元测试捕获具体的错误，基于属性的测试验证一般正确性。

### 单元测试

#### 测试框架
- **Python后端**：pytest
- **Flutter前端**：flutter_test (单元测试和Widget测试)

#### 单元测试覆盖范围

**API端点测试**
```python
@pytest.mark.asyncio
async def test_upload_video_success():
    """测试成功上传视频"""
    # 准备测试数据
    video_file = create_test_video_file("test.mp4", size_mb=10)
    metadata = VideoMetadata(title="测试视频", description="测试描述")
    
    # 执行上传
    response = await client.post(
        "/contents/upload",
        files={"video": video_file},
        data={"metadata": metadata.json()}
    )
    
    # 验证响应
    assert response.status_code == 200
    assert "video_id" in response.json()

@pytest.mark.asyncio
async def test_upload_video_exceeds_size_limit():
    """测试上传超大视频被拒绝"""
    # 准备超大文件
    video_file = create_test_video_file("large.mp4", size_mb=1000)
    
    # 执行上传
    response = await client.post(
        "/contents/upload",
        files={"video": video_file}
    )
    
    # 验证被拒绝
    assert response.status_code == 400
    assert "FILE_SIZE_EXCEEDED" in response.json()["code"]
```

**Widget测试（Flutter前端）**
```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:video_platform/widgets/video_uploader.dart';

void main() {
  testWidgets('应该显示上传进度', (WidgetTester tester) async {
    // 构建Widget
    await tester.pumpWidget(
      MaterialApp(
        home: VideoUploader(
          maxSize: 100,
          acceptFormats: ['mp4', 'mov', 'avi'],
          onUploadStart: () {},
          onUploadProgress: (progress) {},
          onUploadComplete: (videoId) {},
          onUploadError: (error) {},
        ),
      ),
    );
    
    // 模拟文件选择
    // ... 触发文件选择逻辑
    
    // 等待Widget更新
    await tester.pump();
    
    // 验证进度显示
    expect(find.byType(LinearProgressIndicator), findsOneWidget);
  });
  
  testWidgets('应该拒绝不支持的格式', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: VideoUploader(
          maxSize: 100,
          acceptFormats: ['mp4', 'mov', 'avi'],
          onUploadStart: () {},
          onUploadProgress: (progress) {},
          onUploadComplete: (videoId) {},
          onUploadError: (error) {},
        ),
      ),
    );
    
    // 尝试上传不支持的格式
    // ... 触发不支持格式的文件选择
    
    await tester.pump();
    
    // 验证错误提示
    expect(find.text('不支持的视频格式'), findsOneWidget);
  });
}
```

### 基于属性的测试

#### 测试框架
- **Python后端**：Hypothesis

#### 基于属性的测试要求

- 每个正确性属性必须由单个基于属性的测试实现
- 每个测试应运行至少100次迭代
- 每个测试必须使用注释明确引用设计文档中的属性
- 使用格式：`# Feature: enterprise-video-learning-platform, Property X: [property text]`

#### 基于属性的测试示例

**属性1：视频格式验证**
```python
from hypothesis import given, strategies as st

# Feature: enterprise-video-learning-platform, Property 1: 视频格式验证
@given(
    filename=st.text(min_size=1),
    extension=st.sampled_from(['mp4', 'mov', 'avi', 'wmv', 'flv', 'mkv'])
)
@settings(max_examples=100)
def test_video_format_validation(filename, extension):
    """
    对于任何上传的视频文件，如果其格式为MP4、MOV或AVI，
    则系统应接受该文件；否则应拒绝
    """
    file_path = f"{filename}.{extension}"
    supported_formats = ['mp4', 'mov', 'avi']
    
    result = validate_video_format(file_path)
    
    if extension.lower() in supported_formats:
        assert result.is_valid is True
    else:
        assert result.is_valid is False
        assert "不支持的视频格式" in result.error_message
```

**属性3：元数据标题必填**
```python
# Feature: enterprise-video-learning-platform, Property 3: 元数据标题必填
@given(
    title=st.one_of(
        st.just(""),
        st.just("   "),
        st.text(alphabet=st.characters(whitelist_categories=('Zs',)), min_size=1)
    )
)
@settings(max_examples=100)
def test_title_required_validation(title):
    """
    对于任何内容保存或提交操作，如果标题字段为空或仅包含空白字符，
    则系统应拒绝该操作
    """
    metadata = VideoMetadata(title=title, description="测试描述")
    
    result = validate_metadata(metadata)
    
    if not title or title.strip() == "":
        assert result.is_valid is False
        assert "标题不能为空" in result.error_message
    else:
        assert result.is_valid is True
```

**属性5：草稿往返一致性**
```python
# Feature: enterprise-video-learning-platform, Property 5: 草稿往返一致性
@given(
    title=st.text(min_size=1, max_size=200),
    description=st.text(max_size=500),
    content_type=st.sampled_from(['工作知识', '生活分享', '企业文化']),
    tags=st.lists(st.text(min_size=1, max_size=20), max_size=10)
)
@settings(max_examples=100)
async def test_draft_round_trip_consistency(title, description, content_type, tags):
    """
    对于任何保存为草稿的内容，重新加载该草稿应返回
    与保存时完全相同的视频和元数据
    """
    # 创建草稿
    original_draft = Draft(
        title=title,
        description=description,
        content_type=content_type,
        tags=tags,
        video_url="https://example.com/video.mp4"
    )
    
    # 保存草稿
    draft_id = await content_service.save_draft(original_draft)
    
    # 重新加载草稿
    loaded_draft = await content_service.load_draft(draft_id)
    
    # 验证一致性
    assert loaded_draft.title == original_draft.title
    assert loaded_draft.description == original_draft.description
    assert loaded_draft.content_type == original_draft.content_type
    assert set(loaded_draft.tags) == set(original_draft.tags)
    assert loaded_draft.video_url == original_draft.video_url
```

**属性19：多筛选器AND逻辑**
```python
# Feature: enterprise-video-learning-platform, Property 19: 多筛选器AND逻辑
@given(
    filters=st.dictionaries(
        keys=st.sampled_from(['content_type', 'position', 'skill']),
        values=st.lists(st.text(min_size=1), min_size=1, max_size=3),
        min_size=2,
        max_size=3
    )
)
@settings(max_examples=100)
async def test_multi_filter_and_logic(filters):
    """
    对于任何应用了多个筛选器的查询，
    返回的所有内容应满足所有筛选条件
    """
    # 执行筛选查询
    results = await content_service.search_with_filters(filters)
    
    # 验证每个结果都满足所有筛选条件
    for content in results:
        for filter_key, filter_values in filters.items():
            content_value = getattr(content, filter_key)
            assert content_value in filter_values, \
                f"内容 {content.id} 的 {filter_key}={content_value} 不在筛选值 {filter_values} 中"
```

**属性23：点赞计数一致性**
```python
# Feature: enterprise-video-learning-platform, Property 23: 点赞计数一致性
@given(
    user_ids=st.lists(st.uuids(), min_size=0, max_size=100, unique=True)
)
@settings(max_examples=100)
async def test_like_count_consistency(user_ids):
    """
    对于任何内容，其点赞计数应等于点赞该内容的唯一用户数量
    """
    # 创建测试内容
    content_id = await create_test_content()
    
    # 模拟用户点赞
    for user_id in user_ids:
        await interaction_service.like_content(user_id, content_id)
    
    # 获取内容信息
    content = await content_service.get_content(content_id)
    
    # 验证点赞计数
    assert content.like_count == len(user_ids)
    
    # 验证数据库中的点赞记录数
    like_records = await db.query(Interaction).filter(
        Interaction.content_id == content_id,
        Interaction.type == InteractionType.LIKE
    ).count()
    assert like_records == len(user_ids)
```

### 集成测试

**端到端内容发布流程**
```python
@pytest.mark.integration
async def test_end_to_end_content_publishing():
    """测试完整的内容发布流程"""
    # 1. 用户上传视频
    video_id = await upload_test_video()
    
    # 2. 提交审核
    await submit_for_review(video_id)
    
    # 3. 管理员批准
    await approve_content(video_id)
    
    # 4. 验证内容已发布
    content = await get_content(video_id)
    assert content.status == ContentStatus.PUBLISHED
    
    # 5. 验证内容出现在推荐流中
    recommended = await get_recommended_content(user_id)
    assert any(c.id == video_id for c in recommended)
```

### 性能测试

**负载测试**
```python
from locust import HttpUser, task, between

class VideoUploadUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def upload_video(self):
        """模拟视频上传"""
        files = {'video': open('test_video.mp4', 'rb')}
        self.client.post("/contents/upload", files=files)
    
    @task(3)
    def browse_content(self):
        """模拟浏览内容（更频繁）"""
        self.client.get("/contents/recommended")
```

### 测试数据生成

**测试夹具**
```python
@pytest.fixture
def test_user():
    """创建测试用户"""
    return User(
        id=str(uuid.uuid4()),
        employee_id="TEST001",
        name="测试用户",
        department="技术部",
        position="工程师"
    )

@pytest.fixture
def test_video_file():
    """创建测试视频文件"""
    return create_test_video_file(
        filename="test.mp4",
        duration=30,
        size_mb=10
    )

@pytest.fixture
async def test_content(test_user):
    """创建测试内容"""
    content = Content(
        id=str(uuid.uuid4()),
        title="测试视频",
        description="这是一个测试视频",
        creator_id=test_user.id,
        status=ContentStatus.PUBLISHED
    )
    await db.add(content)
    await db.commit()
    return content
```

### 测试覆盖率目标

- **单元测试覆盖率**：≥ 80%
- **API端点覆盖率**：100%
- **关键业务逻辑覆盖率**：≥ 90%
- **基于属性的测试**：所有正确性属性都有对应的测试

## 部署架构

### AWS部署

系统部署在AWS中国宁夏区域 (cn-northwest-1)，采用云原生架构。

#### 核心AWS服务

**计算层**
- ECS Fargate: 运行容器化的后端服务（API服务、AI服务、用户服务）
- Lambda: 处理异步任务（AI处理、通知发送、数据统计）

**存储层**
- S3: 存储视频文件、封面图片、用户头像（生产环境）
- RDS for MySQL (Multi-AZ): 关系型数据库，高可用部署（生产环境）
- 开发/测试环境：Docker MySQL + 本地文件系统

**网络层**
- VPC: 虚拟私有云，多AZ部署
- Application Load Balancer: 应用负载均衡
- CloudFront: CDN加速视频和静态资源分发
- Route 53: DNS服务

**安全层**
- WAF: Web应用防火墙
- Shield: DDoS防护
- Secrets Manager: 密钥管理
- IAM: 身份和访问管理

**监控层**
- CloudWatch: 监控、日志和告警
- X-Ray: 分布式追踪
- CloudTrail: API调用审计

#### 高可用架构（生产环境）

- 多可用区部署（至少2个AZ）
- RDS Multi-AZ自动故障转移
- ECS服务自动扩展
- S3跨区域复制（可选）

#### 开发/测试环境

- Docker Compose部署
- MySQL容器（单实例）
- 本地文件系统存储
- 简化的服务配置

#### 扩展策略（生产环境）

**水平扩展**
- ECS服务根据CPU/内存使用率自动扩展
- RDS读副本分离读写负载

**垂直扩展**
- 根据负载调整实例规格
- 使用Reserved Instances优化成本

#### 成本优化

- 使用Spot实例运行非关键任务
- S3 Intelligent-Tiering自动优化存储成本
- CloudFront减少S3请求成本
- Reserved Instances降低RDS成本
- 设置成本告警

### Flutter Web部署

Flutter应用编译为Web后，部署到S3 + CloudFront：

```
Flutter项目
    ↓
flutter build web
    ↓
上传到S3 bucket
    ↓
CloudFront分发
    ↓
企业App WebView加载
```

### 监控和告警

**关键指标**
- API响应时间 < 2s
- 错误率 < 1%
- 视频上传成功率 > 99%
- AI处理成功率 > 95%
- 数据库连接池使用率 < 80%

**告警通知**
- CloudWatch Alarms → SNS → 企业微信/邮件

