#!/bin/bash
# 启动后端API服务器

echo "========================================="
echo "启动NL2SQL后端API服务器"
echo "========================================="

# 进入项目根目录
cd "$(dirname "$0")/.."

# Conda环境名称
CONDA_ENV_NAME="${CONDA_ENV_NAME:-web_sql}"

# 检查conda是否可用
if command -v conda &> /dev/null; then
    echo "检测到Conda环境，使用conda..."
    
    # 初始化conda（为了在脚本中使用conda activate）
    eval "$(conda shell.bash hook)"
    
    # 检查环境是否存在
    if conda env list | grep -q "^${CONDA_ENV_NAME} "; then
        echo "激活Conda环境: ${CONDA_ENV_NAME}"
        conda activate ${CONDA_ENV_NAME}
    else
        echo "错误: Conda环境 '${CONDA_ENV_NAME}' 不存在"
        echo "请先创建环境: conda create -n ${CONDA_ENV_NAME} python=3.10"
        exit 1
    fi
    
    # 检查是否安装了依赖
    if ! python -c "import fastapi" 2>/dev/null; then
        echo "正在安装后端依赖..."
        pip install -r backend_requirements.txt
    fi
    
elif [ -d "venv" ]; then
    echo "使用Python venv虚拟环境..."
    source venv/bin/activate
    
    # 检查是否安装了依赖
    if ! python -c "import fastapi" 2>/dev/null; then
        echo "正在安装后端依赖..."
        pip install -r backend_requirements.txt
    fi
    
else
    echo "错误: 未找到conda或venv环境"
    echo ""
    echo "请选择以下方式之一:"
    echo "1. 使用conda: conda create -n web_sql python=3.10"
    echo "2. 使用venv: python3 -m venv venv"
    exit 1
fi

# 设置环境变量
export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-8000}"

echo ""
echo "API地址: http://${HOST}:${PORT}"
echo "API文档: http://${HOST}:${PORT}/docs"
echo "========================================="

# 启动服务器
python app.py

