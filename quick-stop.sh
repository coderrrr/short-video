#!/bin/bash
# 企业短视频学习平台 - 快速停止脚本

set -e

echo "=========================================="
echo "企业短视频学习平台 - 停止服务"
echo "=========================================="
echo ""

# 停止管理后台
if [ -f logs/admin-web.pid ]; then
    echo "停止管理后台..."
    PID=$(cat logs/admin-web.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null || true
        echo "管理后台已停止 (PID: $PID)"
    else
        echo "管理后台进程不存在"
    fi
    rm -f logs/admin-web.pid
else
    echo "管理后台未运行（未找到 PID 文件）"
fi

echo ""

# 停止后端服务
echo "停止后端服务..."
docker compose stop

echo ""
echo "=========================================="
echo "所有服务已停止！"
echo "=========================================="
echo ""
echo "重新启动服务："
echo "  ./quick-start.sh"
echo ""
echo "完全清理（包括数据）："
echo "  docker compose down -v"
echo ""
