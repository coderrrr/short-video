#!/bin/bash
# 企业短视频学习平台 - 快速启动脚本

set -e

echo "=========================================="
echo "企业短视频学习平台 - 快速启动"
echo "=========================================="
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "错误：未检测到 Docker，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker compose &> /dev/null; then
    echo "错误：未检测到 Docker Compose，请先安装 Docker Compose"
    exit 1
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "创建 .env 文件..."
    cp .env.example .env
    echo ""
    echo "提示：请编辑 .env 文件配置以下必需项："
    echo "  - JWT_SECRET_KEY: JWT 密钥（生产环境必须修改）"
    echo ""
fi

# 创建必需目录
echo "创建必需目录..."
mkdir -p data/mysql
mkdir -p storage/{videos,covers,avatars,temp}
mkdir -p logs/{backend,nginx,mysql}
mkdir -p backups

# 启动服务
echo ""
echo "启动服务..."
docker compose up -d

# 等待 MySQL 启动
echo ""
echo "等待 MySQL 启动..."
sleep 10

# 检查 MySQL 健康状态
echo "检查 MySQL 健康状态..."
for i in {1..30}; do
    if docker compose exec -T mysql mysqladmin ping -h localhost -u root -p${MYSQL_ROOT_PASSWORD:-root_password} &> /dev/null; then
        echo "MySQL 已就绪！"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "错误：MySQL 启动超时"
        docker compose logs mysql
        exit 1
    fi
    echo "等待 MySQL 启动... ($i/30)"
    sleep 2
done

# 检查数据库是否已存在
echo ""
echo "检查数据库..."
DB_EXISTS=$(docker compose exec -T mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD:-root_password} -e "SHOW DATABASES LIKE 'short_video';" | grep -c "short_video" || true)

if [ "$DB_EXISTS" -eq 0 ]; then
    echo "数据库不存在，开始初始化..."
    docker compose exec -T mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD:-root_password} < database/create_database.sql
    docker compose exec -T mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD:-root_password} short_video < database/create_tables.sql
    echo "数据库初始化完成！"
else
    echo "数据库已存在，跳过初始化"
fi

# 检查 Node.js 是否安装
echo ""
if command -v node &> /dev/null; then
    echo "检测到 Node.js，准备启动管理后台..."
    
    # 检查 admin-web 依赖是否已安装
    if [ ! -d "admin-web/node_modules" ]; then
        echo "安装管理后台依赖..."
        cd admin-web
        npm install
        cd ..
    fi
    
    # 启动管理后台（后台运行）
    echo "启动管理后台..."
    cd admin-web
    nohup npm run dev > ../logs/admin-web.log 2>&1 &
    ADMIN_PID=$!
    cd ..
    
    # 等待管理后台启动
    echo "等待管理后台启动..."
    sleep 5
    
    # 检查管理后台是否成功启动
    if ps -p $ADMIN_PID > /dev/null; then
        echo "管理后台已启动！(PID: $ADMIN_PID)"
        echo $ADMIN_PID > logs/admin-web.pid
    else
        echo "警告：管理后台启动失败，请查看日志: logs/admin-web.log"
    fi
else
    echo "未检测到 Node.js，跳过管理后台启动"
    echo "如需启动管理后台，请先安装 Node.js 18+，然后运行："
    echo "  cd admin-web && npm install && npm run dev"
fi

# 显示服务状态
echo ""
echo "=========================================="
echo "服务启动成功！"
echo "=========================================="
echo ""
docker compose ps
echo ""
echo "访问地址："
echo "  - 后端 API: http://localhost:8000"
echo "  - API 文档: http://localhost:8000/docs"
echo "  - 健康检查: http://localhost:8000/health"

if command -v node &> /dev/null && [ -f logs/admin-web.pid ]; then
    echo "  - 管理后台: http://localhost:5173"
fi

echo ""
echo "其他前端服务："
echo "  - 用户端(Flutter Web): cd frontend && flutter run -d web-server --web-port 8080"
echo ""
echo "常用命令："
echo "  - 查看后端日志: docker compose logs -f backend"
echo "  - 查看管理后台日志: tail -f logs/admin-web.log"
echo "  - 停止后端服务: docker compose stop"
echo "  - 停止管理后台: kill \$(cat logs/admin-web.pid)"
echo "  - 重启服务: docker compose restart"
echo "  - 查看帮助: make help"
echo ""
echo "详细文档请参考: README.md"
echo ""
