#!/bin/bash
# 同时启动前后端服务

echo "========================================="
echo "启动NL2SQL完整系统"
echo "========================================="

# 进入项目根目录
cd "$(dirname "$0")/.."

# 启动后端（后台运行）
echo "启动后端服务..."
./scripts/start_backend.sh &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "启动前端服务..."
./scripts/start_frontend.sh &
FRONTEND_PID=$!

echo ""
echo "========================================="
echo "系统启动完成！"
echo "后端API: http://localhost:8000"
echo "前端界面: http://localhost:5173"
echo "API文档: http://localhost:8000/docs"
echo "========================================="
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait

