#!/bin/bash
# 启动前端开发服务器

echo "========================================="
echo "启动NL2SQL前端开发服务器"
echo "========================================="

# 进入项目根目录
cd "$(dirname "$0")/.."

# 检查Node.js环境
if ! command -v npm &> /dev/null; then
    echo "错误: 未找到npm，请先安装Node.js"
    exit 1
fi

# 检查是否安装了依赖
if [ ! -d "node_modules" ]; then
    echo "正在安装前端依赖..."
    npm install
fi

echo "前端地址: http://localhost:5173"
echo "========================================="

# 启动开发服务器
npm run dev

