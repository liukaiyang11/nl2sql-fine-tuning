# Conda环境安装指南

## 🎯 使用Conda环境（推荐for macOS）

既然您使用conda，这是最简单的方式！

---

## 📦 完整安装步骤

### 第一步：创建Conda环境

```bash
# 创建名为web_sql的conda环境（Python 3.10）
conda create -n web_sql python=3.10 -y

# 或者如果您已经创建了，跳过此步骤
```

### 第二步：激活环境并安装依赖

```bash
# 激活conda环境
conda activate web_sql

# 进入项目目录
cd /Users/baierfa/Documents/muyan/大模型微调/Ch11_sql微调/Web_shargpt

# 安装后端依赖
pip install -r backend_requirements.txt
```

### 第三步：启动后端

```bash
# 确保在web_sql环境中（命令行前有 (web_sql) 标识）
python app.py
```

应该看到：
```
🚀 NL2SQL数据生成系统API服务器启动
📍 API地址: http://0.0.0.0:8000/api
📍 WebSocket: ws://0.0.0.0:8000/ws
📍 健康检查: http://0.0.0.0:8000/health
📍 API文档: http://0.0.0.0:8000/docs
```

### 第四步：启动前端（新终端）

```bash
cd /Users/baierfa/Documents/muyan/大模型微调/Ch11_sql微调/Web_shargpt

# 启动前端开发服务器
npm run dev
```

### 第五步：访问Web界面

打开浏览器访问前端显示的地址（通常是 `http://localhost:3000` 或 `http://localhost:5173`）

---

## 🚀 使用启动脚本

现在启动脚本已支持conda，可以直接运行：

### 方式一：使用脚本启动后端

```bash
# 脚本会自动检测并激活conda环境
./scripts/start_backend.sh
```

### 方式二：手动启动（更可控）

**终端1 - 后端：**
```bash
conda activate web_sql
cd Web_shargpt
python app.py
```

**终端2 - 前端：**
```bash
cd Web_shargpt
npm run dev
```

---

## 📋 依赖检查

验证所有依赖是否正确安装：

```bash
# 激活环境
conda activate web_sql

# 检查关键依赖
python -c "import fastapi, uvicorn, pymysql, openai, sqlglot; print('✅ 所有依赖已正确安装')"
```

如果看到 `✅ 所有依赖已正确安装`，说明环境配置成功！

---

## 🔧 Conda常用命令

```bash
# 查看所有conda环境
conda env list

# 激活环境
conda activate web_sql

# 退出环境
conda deactivate

# 查看当前环境的包
conda list

# 删除环境（如果需要重新创建）
conda env remove -n web_sql
```

---

## 📥 下载生成的数据

生成完成后，有三种方式获取数据：

### 方式1：Web界面下载

点击界面上的"**下载数据**"按钮

### 方式2：API下载

```bash
# 下载最新的训练数据
curl -O http://localhost:8000/api/download/latest

# 下载特定文件
curl -O http://localhost:8000/api/download/nl2sql.jsonl
curl -O http://localhost:8000/api/download/metadata.json
curl -O http://localhost:8000/api/download/plan.json
```

### 方式3：直接从文件系统

```bash
cd /Users/baierfa/Documents/muyan/大模型微调/Ch11_sql微调/Web_shargpt/data

# 查看所有生成的文件
ls -lh

# 打开Finder查看
open .
```

**重要文件：**
- ✅ **`nl2sql.jsonl`** - 最终训练数据（用于LLaMA-Factory）
- `metadata.json` - 数据库元数据
- `table_cards.json` - 表卡片摘要
- `plan.json` - 主题规划
- `samples_raw.jsonl` - 原始样本
- `samples_valid.jsonl` - 验证通过的样本

---

## 🎯 完整工作流程

### 1. 配置数据库

在Web界面的"数据库设置"面板：
- 数据库类型：MySQL
- 主机：localhost 或 127.0.0.1 或您的服务器IP
- 端口：3306
- 用户名：root
- 密码：您的密码
- 数据库名：your_database

点击"**测试连接**"验证配置

### 2. 配置LLM

在"模型设置"面板：
- API端点：您的LLM服务地址
- 模型名称：如 qwen2.5-7b-instruct
- API密钥：您的密钥
- Temperature：0.5-0.7（推荐）
- Top P：0.9

点击"**测试连接**"验证配置

### 3. 设置生成参数

在"生成参数"面板：
- SQL方言：MySQL
- 数据格式：Alpaca（推荐用于LLaMA-Factory）
- 样本数量：100（测试）或 500+（正式）
- 输出路径：./data/nl2sql.jsonl
- 启用验证：✅ 开启（推荐）

### 4. 开始生成

点击"**开始生成**"按钮，实时查看：
- 6个步骤的进度
- 详细的执行日志
- 生成的样本数量

### 5. 下载数据

生成完成后：
1. 点击"**下载数据**"按钮
2. 或者从 `data/nl2sql.jsonl` 直接获取

---

## ⚠️ 常见问题

### Q1: conda activate失败

```bash
# 初始化conda
conda init bash
# 或
conda init zsh

# 重启终端后再试
conda activate web_sql
```

### Q2: 依赖安装失败

```bash
# 使用conda安装一些基础包
conda install -c conda-forge pymysql sqlglot

# 其余用pip安装
pip install -r backend_requirements.txt
```

### Q3: 端口8000被占用

```bash
# 查看占用
lsof -i :8000

# 换端口启动
export PORT=8001
python app.py
```

### Q4: 前端无法连接后端

1. 确认后端正常：访问 `http://localhost:8000/health`
2. 查看浏览器控制台错误
3. 检查CORS设置（已配置允许跨域）

---

## 💡 最佳实践

### 开发环境

1. **后端**：使用conda环境，方便管理依赖
2. **前端**：使用npm开发服务器，支持热更新
3. **数据库**：使用本地测试数据库
4. **LLM**：先用小样本测试（50-100条）

### 生产环境

1. 构建前端：`npm run build`
2. 使用后端服务静态文件
3. 配置Nginx反向代理（可选）
4. 使用生产级数据库

---

## ✅ 环境验证清单

运行前请确认：

- ✅ Conda环境已创建并激活：`conda activate web_sql`
- ✅ 后端依赖已安装：`pip list | grep fastapi`
- ✅ 前端依赖已安装：`ls node_modules`
- ✅ 数据库可访问：`mysql -h host -u user -p`
- ✅ LLM API可访问：`curl your-api-endpoint/health`

---

## 🎉 开始使用

现在您可以：

```bash
# 1. 激活conda环境
conda activate web_sql

# 2. 启动后端
cd Web_shargpt
python app.py

# 3. 新终端启动前端
cd Web_shargpt
npm run dev

# 4. 打开浏览器
# http://localhost:3000 或 http://localhost:5173
```

**祝您使用愉快！** 🚀

---

## 📞 需要帮助？

- 📖 查看 [README.md](README.md) - 完整文档
- 📖 查看 [WEB_USAGE.md](WEB_USAGE.md) - Web界面使用指南
- 📖 查看 [API.md](API.md) - API接口文档
- 🐛 遇到问题？检查日志：`tail -f logs/*.log`

