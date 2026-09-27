#!/bin/bash
# 构建前端并部署

echo "========================================="
echo "构建前端项目"
echo "========================================="

# 进入项目根目录
cd "$(dirname "$0")/.."

# 检查Node.js环境
if ! command -v npm &> /dev/null; then
    echo "错误: 未找到npm，请先安装Node.js"
    exit 1
fi

# 安装依赖
if [ ! -d "node_modules" ]; then
    echo "正在安装前端依赖..."
    npm install
fi

# 构建前端
echo "正在构建前端..."
npm run build

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "✅ 构建成功！"
    echo "构建文件位于: dist/"
    echo "现在可以运行后端服务器访问完整应用"
    echo ""
    echo "启动后端:"
    echo "  cd /Users/baierfa/Documents/muyan/大模型微调/Ch11_sql微调/Web_shargpt"
    echo "  source venv/bin/activate"
    echo "  python app.py"
    echo ""
    echo "访问: http://localhost:8000"
    echo "========================================="
else
    echo "❌ 构建失败"
    exit 1
fi

