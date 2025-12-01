# 企业视频平台管理后台

基于 Vue 3 + Vite + Element Plus 构建的管理后台系统。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite
- **UI 组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP 客户端**: Axios
- **图表库**: ECharts

## 项目结构

```
admin-web/
├── src/
│   ├── api/              # API 接口定义
│   │   ├── request.js    # Axios 封装
│   │   ├── auth.js       # 认证相关 API
│   │   ├── content.js    # 内容管理 API
│   │   ├── review.js     # 审核管理 API
│   │   ├── tag.js        # 标签管理 API
│   │   ├── category.js   # 分类管理 API
│   │   └── analytics.js  # 数据分析 API
│   ├── layouts/          # 布局组件
│   │   └── MainLayout.vue
│   ├── router/           # 路由配置
│   │   └── index.js
│   ├── stores/           # Pinia 状态管理
│   │   ├── index.js
│   │   └── user.js
│   ├── views/            # 页面组件
│   │   ├── Dashboard.vue
│   │   ├── Login.vue
│   │   ├── content/      # 内容管理页面
│   │   ├── review/       # 审核管理页面
│   │   ├── tags/         # 标签管理页面
│   │   ├── categories/   # 分类管理页面
│   │   └── analytics/    # 数据分析页面
│   ├── App.vue
│   └── main.js
├── .env.development      # 开发环境配置
├── .env.production       # 生产环境配置
└── vite.config.js
```

## 开发指南

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 功能模块

### 已实现

- ✅ 项目基础架构
- ✅ Vue Router 路由配置
- ✅ Pinia 状态管理
- ✅ Axios API 客户端封装
- ✅ 主布局（侧边栏、顶部导航、面包屑）
- ✅ 登录页面
- ✅ 路由守卫（认证检查）
- ✅ 内容管理功能（列表、上传、编辑、删除）
- ✅ 审核管理功能（审核队列、批量审核）
- ✅ 标签和分类管理（CRUD、层次结构）
- ✅ KOL账号管理
- ✅ 数据分析功能（内容分析、用户互动分析）
- ✅ 举报管理功能

## API 配置

API 基础地址通过环境变量配置：

- 开发环境: `.env.development`
- 生产环境: `.env.production`

```
VITE_API_BASE_URL=http://localhost:8000
```

## 认证机制

- 使用 JWT Token 进行认证
- Token 存储在 localStorage
- 请求拦截器自动添加 Authorization 头
- 响应拦截器处理 401 错误并跳转登录页

## 注意事项

1. 所有 API 接口都需要后端服务支持
2. 当前登录功能为临时实现，实际登录逻辑需要对接后端 API
3. 部分页面为占位页面，将在后续任务中实现完整功能

## 开发规范

- 使用 Vue 3 Composition API
- 使用 `<script setup>` 语法
- 组件命名使用 PascalCase
- 文件命名使用 kebab-case
- 所有用户界面文本使用中文
