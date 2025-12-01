#!/bin/bash

# 性能测试快速运行脚本

echo "=================================="
echo "企业视频学习平台 - 性能测试"
echo "=================================="
echo ""

# 检查后端服务是否运行
echo "检查后端服务状态..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ 后端服务未运行！"
    echo "请先启动后端服务："
    echo "  docker-compose up -d"
    echo "  或"
    echo "  cd backend && conda run -n short-video uvicorn app.main:app"
    exit 1
fi

echo "✓ 后端服务正在运行"
echo ""

# 设置默认参数
USERS=${1:-50}
SPAWN_RATE=${2:-5}
RUN_TIME=${3:-2m}
HOST=${4:-http://localhost:8000}

echo "测试配置："
echo "  并发用户数: $USERS"
echo "  启动速率: $SPAWN_RATE 用户/秒"
echo "  运行时间: $RUN_TIME"
echo "  目标主机: $HOST"
echo ""

# 创建报告目录
REPORT_DIR="performance_reports"
mkdir -p $REPORT_DIR

# 生成报告文件名（带时间戳）
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$REPORT_DIR/performance_report_${TIMESTAMP}.html"

echo "开始性能测试..."
echo "报告将保存到: $REPORT_FILE"
echo ""

# 运行Locust性能测试
cd "$(dirname "$0")/.."
conda run -n short-video locust \
    -f tests/locustfile.py \
    --host=$HOST \
    --users $USERS \
    --spawn-rate $SPAWN_RATE \
    --run-time $RUN_TIME \
    --headless \
    --html $REPORT_FILE \
    --csv $REPORT_DIR/performance_stats_${TIMESTAMP}

# 检查测试结果
if [ $? -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "✓ 性能测试完成！"
    echo "=================================="
    echo ""
    echo "查看报告："
    echo "  HTML报告: $REPORT_FILE"
    echo "  CSV统计: $REPORT_DIR/performance_stats_${TIMESTAMP}_stats.csv"
    echo ""
    echo "在浏览器中打开报告："
    echo "  open $REPORT_FILE"
else
    echo ""
    echo "=================================="
    echo "❌ 性能测试失败"
    echo "=================================="
    exit 1
fi
