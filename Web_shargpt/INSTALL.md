# 安装和启动指南

## 问题：macOS Python环境管理错误

如果您遇到 `externally-managed-environment` 错误，这是因为macOS使用Homebrew管理Python，不允许直接安装系统级包。

## ✅ 解决方案：使用虚拟环境

### 方法一：自动安装（推荐）

我们已经更新了启动脚本，会自动创建和管理虚拟环境：

```bash
# 直接运行，脚本会自动处理虚拟环境
./scripts/start_backend.sh
```

### 方法二：手动安装

如果自动脚本有问题，可以手动操作：

```bash
# 1. 创建虚拟环境
python3 -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 安装依赖
pip install -r backend_requirements.txt

# 4. 启动后端
python app.py
```

### 方法三：使用pipx（适合全局安装）

```bash
# 安装pipx
brew install pipx

# 使用pipx安装依赖（不推荐，因为依赖很多）
```

## 🚀 完整启动流程

### 步骤1：准备后端环境

```bash
cd /Users/baierfa/Documents/muyan/大模型微调/Ch11_sql微调/Web_shargpt

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r backend_requirements.txt
```

### 步骤2：启动后端

```bash
# 确保在虚拟环境中
python app.py
```

您应该看到：
```
🚀 NL2SQL数据生成系统API服务器启动
📍 API地址: http://0.0.0.0:8000/api
📍 WebSocket: ws://0.0.0.0:8000/ws
📍 健康检查: http://0.0.0.0:8000/health
📍 API文档: http://0.0.0.0:8000/docs
```

### 步骤3：启动前端（新终端）

```bash
cd /Users/baierfa/Documents/muyan/大模型微调/Ch11_sql微调/Web_shargpt

# 如果没有安装过依赖
npm install

# 启动前端
npm run dev
```

### 步骤4：访问界面

打开浏览器访问：`http://localhost:3000` 或 `http://localhost:5173`

（Vite会自动选择可用端口）

## 📥 下载数据

生成完成后，有三种方式下载数据：

### 方式1：通过界面下载

点击界面上的"**下载数据**"按钮

### 方式2：直接访问API

```bash
# 下载最新的训练数据
curl -O http://localhost:8000/api/download/latest

# 下载特定文件
curl -O http://localhost:8000/api/download/nl2sql.jsonl
curl -O http://localhost:8000/api/download/metadata.json
```

### 方式3：从文件系统获取

```bash
cd /Users/baierfa/Documents/muyan/大模型微调/Ch11_sql微调/Web_shargpt/data
ls -lh *.jsonl
```

文件说明：
- `nl2sql.jsonl` - 最终训练数据（这是您需要的）
- `metadata.json` - 数据库元数据
- `table_cards.json` - 表卡片
- `plan.json` - 主题规划
- `samples_raw.jsonl` - 原始样本
- `samples_valid.jsonl` - 验证通过的样本

## 🔧 常见问题

### Q1: 虚拟环境创建失败

```bash
# 确保使用Python 3.8+
python3 --version

# 如果版本太旧，使用Homebrew安装新版本
brew install python@3.11
python3.11 -m venv venv
```

### Q2: 后端启动后立即退出

检查是否有端口占用：
```bash
# 查看8000端口
lsof -i :8000

# 如果被占用，杀掉进程或换端口
export PORT=8001
python app.py
```

### Q3: 前端无法连接后端

1. 确认后端正常运行：访问 `http://localhost:8000/health`
2. 检查前端API配置（如果有配置文件）
3. 查看浏览器控制台错误信息

### Q4: 下载按钮不显示或无效

1. 确认任务已完成（进度100%）
2. 检查 `data/nl2sql.jsonl` 文件是否存在
3. 查看后端日志是否有错误

## 🎯 推荐启动方式

### 开发环境

**终端1（后端）：**
```bash
cd Web_shargpt
source venv/bin/activate  # 如果已创建
python app.py
```

**终端2（前端）：**
```bash
cd Web_shargpt
npm run dev
```

### 生产环境

```bash
# 1. 构建前端
npm run build

# 2. 启动后端（会自动服务前端静态文件）
source venv/bin/activate
python app.py

# 3. 访问
# http://localhost:8000
```

## 📝 环境变量

您可以设置这些环境变量来自定义配置：

```bash
# 后端配置
export HOST=0.0.0.0
export PORT=8000

# 启动
python app.py
```

## ✅ 验证安装

运行以下命令验证环境：

```bash
# 激活虚拟环境
source venv/bin/activate

# 测试导入
python -c "import fastapi, uvicorn, pymysql, openai, sqlglot; print('所有依赖已正确安装')"
```

如果没有错误，说明环境配置成功！

---

**现在您可以正常使用系统了！** 🎉

