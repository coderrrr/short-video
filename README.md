# 企业短视频学习平台

企业内部短视频平台，支持视频上传、内容管理、智能推荐等功能。

> **注意：** 本项目不使用任何LLM/AI功能。标签由管理员手动分配，内容审核由人工完成。

## 目录

- [项目概述](#项目概述)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [开发环境设置](#开发环境设置)
- [项目结构](#项目结构)
- [测试](#测试)
- [常见问题](#常见问题)
- [文档](#文档)
- [贡献指南](#贡献指南)

## 项目概述

本项目是一个面向企业内部的短视频学习平台，旨在鼓励员工创作和分享工作知识与美好生活，丰富企业文化。系统采用前后端分离架构，C端以H5方式集成在企业现有App中，管理端提供PC Web界面。

### 核心功能

- 📱 **移动端视频浏览和互动** - Flutter开发，可编译为Web/H5或Native App
- 🎬 **视频上传和管理** - 支持相机拍摄、相册导入、视频编辑
- 🏷️ **手动标签管理系统** - 多维标签体系（角色、主题、形式、质量、推荐）
- 🎯 **基于规则的推荐系统** - 根据用户角色和观看历史推荐内容
- 👥 **用户互动** - 点赞、评论、收藏、关注、分享
- 📚 **学习计划** - 专题、合集、个性化学习路径
- 📊 **数据统计和分析** - 内容性能分析、用户行为分析
- 🛡️ **人工内容审核** - 平台审核 + 专家二审
- 🎮 **游戏化激励** - 排行榜、徽章、成就系统

### 设计理念

- **简单易用** - 降低创作门槛，鼓励全员参与
- **人工管理** - 标签由管理员手动分配，内容由人工审核，确保质量
- **移动优先** - 针对移动端优化，支持碎片化学习
- **企业文化** - 传播企业价值观，增强团队凝聚力

## 技术栈

### 前端

| 组件 | 技术栈 |
|------|--------|
| **C端** | Flutter (可编译为Web/H5或Native App) |
| **管理端** | Vue 3 + Vite + Element Plus |

### 后端

| 组件 | 技术 |
|------|------|
| **语言** | Python 3.12+ |
| **框架** | FastAPI |
| **ORM** | SQLAlchemy |
| **数据库** | MySQL 8.0 (开发: Docker, 生产: AWS RDS) |
| **存储** | 本地文件系统 (开发), AWS S3 (生产) |

### 部署

| 环境 | 方案 |
|------|------|
| **开发环境** | Docker Compose |
| **生产环境** | AWS中国宁夏区域 (ECS Fargate + CloudFront + ALB) |

## 快速开始

### 前置要求

#### 必需软件

- **Docker** 20.10+ & **Docker Compose** 2.0+ - [下载地址](https://www.docker.com/get-started)
- **Python** 3.12+ (推荐使用Conda) - [下载地址](https://www.anaconda.com/download)
- **Git** - [下载地址](https://git-scm.com/downloads)

#### 可选软件（前端开发）

- **Flutter SDK** 3.x+ - [下载地址](https://flutter.dev/docs/get-started/install)
- **Node.js** 18+ - [下载地址](https://nodejs.org/)

### 三种启动方式

#### 方式一：快速启动脚本（推荐）

```bash
./quick-start.sh
```

脚本会自动完成：
- 检查 Docker 环境
- 创建配置文件和必需目录
- 启动后端服务和数据库
- 初始化数据库表结构
- 自动启动管理后台（如果已安装 Node.js）

启动后可访问：
- 后端 API: http://localhost:8000
- 管理后台: http://localhost:5173（需要 Node.js）
- 默认管理员账号: `ADMIN001` / `admin123`

#### 方式二：Makefile

```bash
make help         # 查看所有可用命令
make setup        # 初始化项目（首次运行）
make start        # 启动后端服务
make init-db      # 初始化数据库（首次运行）
make start-admin  # 启动管理后台
make logs         # 查看日志
make stop         # 停止服务
```

完整启动流程：
```bash
make setup        # 首次运行：初始化项目
make start        # 启动后端和数据库
make init-db      # 首次运行：初始化数据库
make start-admin  # 启动管理后台
```

#### 方式三：手动启动

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置 JWT_SECRET_KEY 等必需项

# 2. 创建必需目录
mkdir -p data/mysql storage/{videos,covers,avatars,temp} logs/{backend,nginx}

# 3. 启动服务
docker-compose up -d

# 4. 首次启动：创建数据库和表结构
# 等待MySQL容器完全启动（约10-30秒）
docker-compose logs -f mysql  # 等待看到 "ready for connections" 消息后按 Ctrl+C

# 执行数据库初始化脚本
docker-compose exec -T mysql mysql -uroot -proot_password < database/create_database.sql
docker-compose exec -T mysql mysql -uroot -proot_password short_video < database/create_tables.sql

```

### 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| **后端 API** | http://localhost:8000 | 自动启动 |
| **API 文档** | http://localhost:8000/docs | 自动启动 |
| **健康检查** | http://localhost:8000/health | 自动启动 |
| **管理后台** | http://localhost:5173 | 快速启动脚本自动启动（需 Node.js） |
| **用户端** | http://localhost:8080 | 需手动启动（需 Flutter） |

**默认管理员账号：**
- 员工ID: `ADMIN001`
- 密码: `admin123`

### 手动启动前端服务

#### 管理后台（Vue）

如果快速启动脚本未自动启动管理后台，可手动启动：

```bash
cd admin-web
npm install
npm run dev
```

访问 http://localhost:5173

#### 用户端（Flutter Web）

```bash
cd frontend
flutter pub get
flutter run -d web-server --web-port 8080
```

访问 http://localhost:8080

## 开发环境设置

### 详细设置步骤

#### 1. 克隆项目

```bash
git clone <repository-url>
cd short-video
```

#### 2. 创建Conda环境

```bash
conda create -n short-video python=3.12
conda activate short-video
```

#### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置以下必需项：
# - DATABASE_URL: 数据库连接字符串
# - JWT_SECRET_KEY: JWT密钥（生产环境必须修改）
```

#### 4. 启动MySQL数据库并初始化

```bash
# 启动MySQL容器
docker-compose up -d mysql

# 等待MySQL完全启动
docker-compose logs -f mysql  # 等待 "ready for connections" 消息后按 Ctrl+C

# 首次启动：执行数据库初始化
docker-compose exec -T mysql mysql -uroot -proot_password < database/create_database.sql
docker-compose exec -T mysql mysql -uroot -proot_password short_video < database/create_tables.sql
```

> **注意**：数据库初始化脚本只需在首次启动时执行一次。如果数据库已存在，可以跳过此步骤。

#### 5. 安装后端依赖

```bash
conda run -n short-video pip install -r backend/requirements.txt
```

如遇问题，可先安装核心依赖：
```bash
conda run -n short-video pip install fastapi uvicorn sqlalchemy aiomysql pydantic pydantic-settings
```



#### 7. 启动后端开发服务器

```bash
cd backend
conda run -n short-video uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看API文档。

### 本地开发模式

#### 后端开发（热重载）

```bash
# 仅启动MySQL
docker-compose up -d mysql

# 本地运行后端
cd backend
conda activate short-video
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端开发

**管理后台：**
```bash
cd admin-web
npm install
npm run dev  # http://localhost:5173
```

**用户端：**
```bash
cd frontend
flutter pub get
flutter run -d web-server --web-port 8080  # http://localhost:8080
# 或使用Chrome调试: flutter run -d chrome
```

### 常用命令

| 命令 | 说明 |
|------|------|
| `make ps` 或 `docker-compose ps` | 查看服务状态 |
| `make logs` 或 `docker-compose logs -f` | 查看后端日志 |
| `make logs-admin` | 查看管理后台日志 |
| `make shell-backend` | 进入后端容器 |
| `make test` | 运行测试 |
| `make init-db` | 初始化数据库 |
| `make backup` | 备份数据库 |
| `make restart` | 重启后端服务 |
| `make start-admin` | 启动管理后台 |
| `make stop-admin` | 停止管理后台 |

## 项目结构

```
enterprise-video-learning-platform/
├── .kiro/                          # Kiro配置和规范文档
│   ├── specs/                      # 项目规格说明
│   │   └── enterprise-video-learning-platform/
│   │       ├── requirements.md     # 需求文档（49个功能需求）
│   │       ├── design.md           # 设计文档
│   │       ├── tasks.md            # 任务列表（41个阶段）
│   │       └── database-schema.sql # 数据库架构
│   └── steering/                   # 开发指导规则
│       ├── python-environment.md
│       ├── chinese-language-requirement.md
│       └── aws-deployment.md
├── backend/                        # 后端服务（FastAPI + Python）
│   ├── app/
│   │   ├── api/                    # API路由（15个模块）
│   │   ├── models/                 # 数据模型（18个模型）
│   │   ├── schemas/                # Pydantic模式
│   │   ├── services/               # 业务逻辑层
│   │   └── utils/                  # 工具函数
│   ├── tests/                      # 测试文件
│   └── requirements.txt
├── frontend/                       # Flutter C端应用
│   ├── lib/
│   │   ├── screens/                # 页面（25个屏幕）
│   │   ├── widgets/                # 组件
│   │   ├── services/               # API服务
│   │   └── models/                 # 数据模型
│   └── pubspec.yaml
├── admin-web/                      # 管理后台（Vue 3）
│   ├── src/
│   │   ├── views/                  # 页面组件
│   │   ├── api/                    # API接口
│   │   └── stores/                 # 状态管理
│   └── package.json
├── docs/                           # 项目文档
├── storage/                        # 本地存储（开发环境）
├── docker-compose.yml
├── Makefile
└── quick-start.sh
```

## 测试

项目采用双重测试策略：**单元测试** + **基于属性的测试（PBT）**

### 运行测试

```bash
# 后端测试
make test
# 或
cd backend && conda run -n short-video pytest

# 运行特定测试
conda run -n short-video pytest backend/tests/test_properties_content.py -v

# 生成覆盖率报告
conda run -n short-video pytest backend/tests --cov=app --cov-report=html

# Flutter测试
cd frontend && flutter test

# 管理后台测试
cd admin-web && npm test
```

### 测试覆盖

- **单元测试**: ~120个，覆盖服务、模型、API
- **集成测试**: 5个，覆盖核心业务流程
- **基于属性的测试**: 6个已实现，26个待实现
- **测试覆盖率目标**: > 80%

详细测试策略请参考 [设计文档](/.kiro/specs/enterprise-video-learning-platform/design.md#测试策略)

## 常见问题

### Q: 如何停止所有服务？

**A**: 
```bash
# 方式一：使用快速停止脚本（推荐）
./quick-stop.sh

# 方式二：使用 Makefile
make stop          # 停止后端服务
make stop-admin    # 停止管理后台

# 方式三：手动停止
docker-compose stop                    # 停止后端服务
kill $(cat logs/admin-web.pid)         # 停止管理后台
```

### Q: 管理后台无法访问？

**A**: 
1. 检查 Node.js 是否已安装：`node --version`（需要 18+）
2. 检查管理后台是否正在运行：`tail -f logs/admin-web.log`
3. 手动启动：`cd admin-web && npm install && npm run dev`
4. 检查端口 5173 是否被占用：`lsof -i :5173`（macOS/Linux）

### Q: Conda环境创建失败

**A**: 确保已正确安装Anaconda或Miniconda，并且conda命令在PATH中。

### Q: Docker容器启动失败

**A**: 
1. 确保Docker Desktop正在运行
2. 检查端口占用：`lsof -i :3306` (macOS/Linux) 或 `netstat -ano | findstr :3306` (Windows)
3. 修改docker-compose.yml中的端口映射

### Q: pip安装依赖超时

**A**: 使用国内镜像源：
```bash
conda run -n short-video pip install -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: Flutter Web 无法正常显示

**A**: 
1. 不要使用 `file://` 协议直接打开 `build/web/index.html`
2. 使用开发服务器：`flutter run -d web-server --web-port 8080`
3. 或使用HTTP服务器：`python -m http.server 8080 -d build/web`

### Q: 数据库迁移失败

**A**: 
1. 确保MySQL容器正在运行：`docker-compose ps`
2. 检查数据库连接配置
3. 查看迁移日志：`docker-compose logs backend`

### Q: 首次启动时如何初始化数据库？

**A**: 
```bash
# 1. 确保MySQL容器正在运行
docker-compose up -d mysql

# 2. 等待MySQL完全启动（约10-30秒）
docker-compose logs -f mysql  # 看到 "ready for connections" 后按 Ctrl+C

# 3. 执行数据库初始化脚本
docker-compose exec -T mysql mysql -uroot -proot_password < database/create_database.sql
docker-compose exec -T mysql mysql -uroot -proot_password short_video < database/create_tables.sql

# 4. 验证数据库是否创建成功
docker-compose exec mysql mysql -uroot -proot_password -e "SHOW DATABASES;"
docker-compose exec mysql mysql -uroot -proot_password short_video -e "SHOW TABLES;"
```

默认管理员账号：
- 员工ID: `ADMIN001`
- 密码: `admin123`

## 文档

### 部署文档

- [本地部署文档](./DEPLOYMENT_LOCAL.md) - 详细的本地开发环境部署指南
- [AWS 部署文档](./DEPLOYMENT_AWS.md) - 生产环境 AWS 部署指南（待完成）

### 项目规格文档

位于 `.kiro/specs/enterprise-video-learning-platform/` 目录：

- [需求文档](/.kiro/specs/enterprise-video-learning-platform/requirements.md) - 49个功能需求
- [设计文档](/.kiro/specs/enterprise-video-learning-platform/design.md) - 架构、数据模型、正确性属性
- [任务列表](/.kiro/specs/enterprise-video-learning-platform/tasks.md) - 41个开发阶段

### 组件文档

- [后端 API 文档](./backend/README.md)
- [管理后台文档](./admin-web/README.md)
- [Flutter 开发指南](./frontend/README.md)
- [安全配置](./backend/SECURITY.md)

### 开发规范

位于 `.kiro/steering/` 目录：

- [Python环境配置](/.kiro/steering/python-environment.md)
- [中文语言要求](/.kiro/steering/chinese-language-requirement.md)
- [AWS部署规范](/.kiro/steering/aws-deployment.md)
- [AI/LLM技术规范](/.kiro/steering/ai-llm-specification.md)

## 贡献指南

详细的贡献指南请参考 [CONTRIBUTING.md](./CONTRIBUTING.md)

### 贡献流程

1. Fork本仓库
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 遵循代码规范（参考 `.kiro/steering/` 目录）
4. 编写测试（单元测试 + 基于属性的测试）
5. 提交更改：`git commit -m 'Add some AmazingFeature'`
6. 推送到分支：`git push origin feature/AmazingFeature`
7. 开启Pull Request

### 代码规范

- **语言**: 所有用户界面和文档使用中文
- **Python**: 遵循PEP 8，使用类型注解，中文注释
- **Flutter**: 遵循Flutter代码风格，使用const构造函数
- **Vue**: 使用Composition API和`<script setup>`语法
- **测试**: 每个新功能都需要单元测试和基于属性的测试（如适用）

## 许可证

本项目为企业内部项目，版权所有。

## 联系方式

如有问题，请联系项目维护团队。
