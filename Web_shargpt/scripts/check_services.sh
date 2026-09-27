#!/bin/bash
# 检查前后端服务状态

echo "========================================="
echo "检查NL2SQL服务状态"
echo "========================================="

# 检查后端
echo ""
echo "1. 检查后端服务 (端口 8000)..."
if lsof -i:8000 > /dev/null 2>&1; then
    echo "✅ 后端服务正在运行"
    curl -s http://localhost:8000/health > /dev/null 2>&1 && echo "   └─ API响应正常" || echo "   └─ ⚠️ API无响应"
else
    echo "❌ 后端服务未运行"
fi

# 检查前端
echo ""
echo "2. 检查前端服务 (端口 5173)..."
if lsof -i:5173 > /dev/null 2>&1; then
    echo "✅ 前端服务正在运行"
    curl -s http://localhost:5173 > /dev/null 2>&1 && echo "   └─ 前端可访问" || echo "   └─ ⚠️ 前端无响应"
else
    echo "❌ 前端服务未运行"
fi

# 检查Python环境
echo ""
echo "3. 检查Python环境..."
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1)
    echo "✅ Python: $PYTHON_VERSION"
    
    # 检查关键依赖
    python -c "import fastapi" 2>/dev/null && echo "   ├─ fastapi ✓" || echo "   ├─ fastapi ✗"
    python -c "import uvicorn" 2>/dev/null && echo "   ├─ uvicorn ✓" || echo "   ├─ uvicorn ✗"
    python -c "import websockets" 2>/dev/null && echo "   └─ websockets ✓" || echo "   └─ websockets ✗"
else
    echo "❌ Python未安装"
fi

# 检查Node环境
echo ""
echo "4. 检查Node环境..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node: $NODE_VERSION"
    
    # 检查npm
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        echo "   └─ npm: $NPM_VERSION"
    fi
else
    echo "❌ Node未安装"
fi

# 检查数据目录
echo ""
echo "5. 检查数据目录..."
DATA_DIR="./data"
if [ -d "$DATA_DIR" ]; then
    FILE_COUNT=$(ls -1 "$DATA_DIR" 2>/dev/null | wc -l | tr -d ' ')
    echo "✅ 数据目录存在"
    echo "   └─ 文件数量: $FILE_COUNT"
    
    if [ -f "$DATA_DIR/nl2sql.jsonl" ]; then
        LINE_COUNT=$(wc -l < "$DATA_DIR/nl2sql.jsonl" | tr -d ' ')
        echo "   └─ nl2sql.jsonl: $LINE_COUNT 行"
    fi
else
    echo "⚠️ 数据目录不存在"
fi

echo ""
echo "========================================="
echo "检查完成"
echo "========================================="
echo ""
echo "💡 提示:"
echo "  - 启动后端: ./scripts/start_backend.sh"
echo "  - 启动前端: ./scripts/start_frontend.sh"
echo "  - 启动全部: ./scripts/start_all.sh"
echo ""

