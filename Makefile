# 企业短视频学习平台 - Makefile
# 简化常用操作的命令集合

.PHONY: help setup start stop restart logs clean test init-db backup start-admin stop-admin logs-admin

# 默认目标：显示帮助信息
help:
	@echo "企业短视频学习平台 - 可用命令："
	@echo ""
	@echo "  make setup          - 初始化项目（首次运行）"
	@echo "  make start          - 启动所有服务"
	@echo "  make start-db       - 仅启动数据库"
	@echo "  make start-backend  - 启动数据库和后端"
	@echo "  make stop           - 停止所有服务"
	@echo "  make restart        - 重启所有服务"
	@echo "  make logs           - 查看所有服务日志"
	@echo "  make logs-backend   - 查看后端日志"
	@echo "  make logs-mysql     - 查看数据库日志"
	@echo "  make ps             - 查看服务状态"
	@echo "  make shell-backend  - 进入后端容器"
	@echo "  make shell-mysql    - 进入数据库容器"
	@echo "  make init-db        - 初始化数据库（首次运行）"
	@echo "  make create-admin   - 创建管理员账号（交互式）"
	@echo "  make create-admin-default - 创建默认管理员账号（快速）"
	@echo "  make start-admin    - 启动管理后台"
	@echo "  make stop-admin     - 停止管理后台"
	@echo "  make logs-admin     - 查看管理后台日志"
	@echo "  make test           - 运行测试"
	@echo "  make test-backend   - 运行后端测试"
	@echo "  make backup         - 备份数据库"
	@echo "  make restore        - 恢复数据库（需要指定 FILE=backup.sql）"
	@echo "  make clean          - 清理容器和数据卷"
	@echo "  make reset          - 重置开发环境（警告：删除所有数据）"
	@echo ""

# 初始化项目
setup:
	@echo "初始化项目..."
	@if [ ! -f .env ]; then \
		echo "创建 .env 文件..."; \
		cp .env.example .env; \
		echo "请编辑 .env 文件配置必需的环境变量"; \
	fi
	@echo "创建必需目录..."
	@mkdir -p data/mysql
	@mkdir -p storage/{videos,covers,avatars,temp}
	@mkdir -p logs/{backend,nginx}
	@echo "安装 Python 依赖..."
	@cd backend && conda run -n short-video pip install -r requirements.txt
	@echo "初始化完成！请运行 'make start' 启动服务"

# 启动服务
start:
	@echo "启动所有服务..."
	@docker-compose up -d
	@echo "等待服务启动..."
	@sleep 5
	@docker-compose ps
	@echo ""
	@echo "服务已启动！"
	@echo "  - 后端 API: http://localhost:8000"
	@echo "  - API 文档: http://localhost:8000/docs"
	@echo "  - 健康检查: http://localhost:8000/health"

start-db:
	@echo "启动数据库..."
	@docker-compose up -d mysql
	@echo "等待数据库启动..."
	@sleep 10
	@docker-compose ps mysql

start-backend:
	@echo "启动数据库和后端..."
	@docker-compose up -d mysql backend
	@echo "等待服务启动..."
	@sleep 10
	@docker-compose ps

# 停止服务
stop:
	@echo "停止所有服务..."
	@docker-compose stop

# 重启服务
restart:
	@echo "重启所有服务..."
	@docker-compose restart
	@docker-compose ps

restart-backend:
	@echo "重启后端服务..."
	@docker-compose restart backend

# 查看日志
logs:
	@docker-compose logs -f

logs-backend:
	@docker-compose logs -f backend

logs-mysql:
	@docker-compose logs -f mysql

# 查看服务状态
ps:
	@docker-compose ps

# 进入容器
shell-backend:
	@docker-compose exec backend bash

shell-mysql:
	@docker-compose exec mysql bash

# 数据库初始化
init-db:
	@echo "初始化数据库..."
	@echo "等待 MySQL 启动..."
	@sleep 5
	@docker-compose exec -T mysql mysql -uroot -p$${MYSQL_ROOT_PASSWORD:-root_password} < database/create_database.sql
	@docker-compose exec -T mysql mysql -uroot -p$${MYSQL_ROOT_PASSWORD:-root_password} short_video < database/create_tables.sql
	@echo "数据库初始化完成！"

# 创建管理员账号
create-admin:
	@echo "创建管理员账号（交互式）..."
	@cd backend && conda run -n short-video python create_admin.py

create-admin-default:
	@echo "创建默认管理员账号..."
	@cd backend && conda run -n short-video python create_default_admin.py
	@echo ""
	@echo "默认管理员账号已创建："
	@echo "  员工ID: ADMIN001"
	@echo "  密码: admin123"
	@echo ""
	@echo "⚠️  请在首次登录后立即修改密码！"

# 测试
test:
	@echo "运行所有测试..."
	@cd backend && conda run -n short-video pytest

test-backend:
	@echo "运行后端测试..."
	@cd backend && conda run -n short-video pytest tests/

test-coverage:
	@echo "运行测试并生成覆盖率报告..."
	@cd backend && conda run -n short-video pytest --cov=app --cov-report=html
	@echo "覆盖率报告已生成：backend/htmlcov/index.html"

# 数据库备份
backup:
	@echo "备份数据库..."
	@mkdir -p backups
	@docker-compose exec mysql mysqldump -u root -p$${MYSQL_ROOT_PASSWORD:-root_password} short_video > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "备份完成：backups/backup_$$(date +%Y%m%d_%H%M%S).sql"

# 数据库恢复
restore:
	@if [ -z "$(FILE)" ]; then \
		echo "错误：请指定备份文件，例如：make restore FILE=backups/backup_20250115_120000.sql"; \
		exit 1; \
	fi
	@echo "恢复数据库从 $(FILE)..."
	@docker-compose exec -T mysql mysql -u root -p$${MYSQL_ROOT_PASSWORD:-root_password} short_video < $(FILE)
	@echo "恢复完成！"

# 清理
clean:
	@echo "清理容器和镜像..."
	@docker-compose down
	@docker system prune -f

clean-all:
	@echo "警告：这将删除所有容器、镜像和数据卷！"
	@read -p "确认继续？(yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker-compose down -v; \
		docker system prune -a -f; \
		echo "清理完成！"; \
	else \
		echo "已取消"; \
	fi

# 重置开发环境
reset:
	@echo "警告：这将删除所有数据并重置开发环境！"
	@read -p "确认继续？(yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		echo "停止服务..."; \
		docker-compose down -v; \
		echo "清理数据目录..."; \
		rm -rf data/mysql/*; \
		rm -rf storage/videos/*; \
		rm -rf storage/covers/*; \
		rm -rf storage/avatars/*; \
		rm -rf storage/temp/*; \
		echo "重新启动服务..."; \
		docker-compose up -d; \
		sleep 10; \
		echo "初始化数据库..."; \
		docker-compose exec -T mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD:-root_password} < database/create_database.sql; \
		docker-compose exec -T mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD:-root_password} short_video < database/create_tables.sql; \
		echo "重置完成！"; \
	else \
		echo "已取消"; \
	fi

# 开发模式：本地运行后端
dev-backend:
	@echo "在本地运行后端（热重载模式）..."
	@cd backend && conda run -n short-video uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 开发模式：本地运行管理后台
dev-admin:
	@echo "在本地运行管理后台..."
	@cd admin-web && npm run dev

# 启动管理后台（后台运行）
start-admin:
	@echo "启动管理后台..."
	@if [ ! -d admin-web/node_modules ]; then \
		echo "安装依赖..."; \
		cd admin-web && npm install; \
	fi
	@mkdir -p logs
	@cd admin-web && nohup npm run dev > ../logs/admin-web.log 2>&1 & echo $$! > ../logs/admin-web.pid
	@sleep 3
	@if [ -f logs/admin-web.pid ] && ps -p $$(cat logs/admin-web.pid) > /dev/null; then \
		echo "管理后台已启动！(PID: $$(cat logs/admin-web.pid))"; \
		echo "访问地址: http://localhost:5173"; \
	else \
		echo "启动失败，请查看日志: logs/admin-web.log"; \
	fi

# 停止管理后台
stop-admin:
	@if [ -f logs/admin-web.pid ]; then \
		echo "停止管理后台..."; \
		kill $$(cat logs/admin-web.pid) 2>/dev/null || true; \
		rm -f logs/admin-web.pid; \
		echo "管理后台已停止"; \
	else \
		echo "管理后台未运行"; \
	fi

# 查看管理后台日志
logs-admin:
	@if [ -f logs/admin-web.log ]; then \
		tail -f logs/admin-web.log; \
	else \
		echo "日志文件不存在: logs/admin-web.log"; \
	fi

# 代码质量检查
lint:
	@echo "运行代码质量检查..."
	@cd backend && conda run -n short-video flake8 app/
	@cd backend && conda run -n short-video black --check app/
	@cd backend && conda run -n short-video mypy app/

# 格式化代码
format:
	@echo "格式化代码..."
	@cd backend && conda run -n short-video black app/
	@cd backend && conda run -n short-video isort app/

# 查看资源使用
stats:
	@docker stats --no-stream

# 健康检查
health:
	@echo "检查服务健康状态..."
	@echo ""
	@echo "MySQL:"
	@docker-compose exec mysql mysqladmin -u root -p$${MYSQL_ROOT_PASSWORD:-root_password} ping || echo "MySQL 不健康"
	@echo ""
	@echo "后端 API:"
	@curl -f http://localhost:8000/health || echo "后端 API 不健康"
	@echo ""
