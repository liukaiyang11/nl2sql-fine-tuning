# 🚀 NL2SQL数据生成系统 - 快速开始

欢迎使用NL2SQL自动化数据生成系统Web版本！

---

## ⚡ 30秒快速启动

### 1. 安装依赖

```bash
# 安装后端依赖
pip install -r backend_requirements.txt

# 安装前端依赖  
npm install
```

### 2. 启动服务

```bash
./scripts/start_all.sh
```

### 3. 访问Web界面

打开浏览器: **http://localhost:5173**

---

## 📖 详细文档

| 文档 | 说明 |
|------|------|
| [README.md](README.md) | 完整的系统文档 |
| [WEB_USAGE.md](WEB_USAGE.md) | Web界面使用指南 |
| [API.md](API.md) | API接口文档 |
| [QUICKSTART.md](QUICKSTART.md) | 命令行快速开始 |

---

## 🎯 快速测试

### 使用示例数据库

```bash
# 导入示例数据库
mysql -u root -p < example_database.sql
```

### 配置Web界面

1. **数据库设置**：
   - 类型：MySQL
   - 主机：localhost
   - 端口：3306
   - 用户：root
   - 数据库：sales_demo

2. **模型设置**：
   - API地址：http://localhost:8000/v1
   - 模型：qwen2.5-7b-instruct
   - API密钥：您的密钥

3. **生成参数**：
   - SQL方言：MySQL
   - 样本数量：50
   - 数据格式：Alpaca

4. 点击"**开始生成**"

---

## 🎨 界面预览

Web界面包含：

1. ✅ **数据库配置面板** - 配置并测试数据库连接
2. ✅ **模型配置面板** - 配置并测试LLM连接
3. ✅ **生成参数面板** - 设置生成选项
4. ✅ **进度监控面板** - 6步进度显示
5. ✅ **实时日志面板** - 详细执行日志

---

## 🔧 启动方式

### 方式一：一键启动（推荐）

```bash
./scripts/start_all.sh
```

同时启动前后端，适合开发和测试。

### 方式二：分别启动

```bash
# 终端1
./scripts/start_backend.sh

# 终端2
./scripts/start_frontend.sh
```

适合调试和独立开发。

### 方式三：生产部署

```bash
# 1. 构建前端
./scripts/build_and_deploy.sh

# 2. 启动后端
python app.py
```

访问：http://localhost:8000

---

## 📊 系统架构

```
┌──────────────────┐
│   Web浏览器      │
│  (React前端)     │
└────────┬─────────┘
         │ HTTP/WebSocket
         ↓
┌────────────────────┐
│  FastAPI后端服务器 │
│  • REST API        │
│  • WebSocket       │
│  • 任务管理        │
└────────┬───────────┘
         │
         ↓
┌────────────────────┐
│  NL2SQL核心模块    │
│  • 元数据提取      │
│  • LLM调用         │
│  • SQL验证         │
│  • 数据导出        │
└────────┬───────────┘
         │
    ┌────┴────┐
    ↓         ↓
┌────────┐ ┌────────┐
│ 数据库 │ │  LLM   │
└────────┘ └────────┘
```

---

## 📦 项目结构

```
Web_shargpt/
├── app.py              # FastAPI主应用
├── api/                # API模块
│   ├── routes.py      # REST API
│   ├── websocket.py   # WebSocket
│   └── task_manager.py # 任务管理
├── modules/           # 核心模块
│   ├── db_connector.py
│   ├── llm_client.py
│   └── ...
├── src/               # React前端
├── scripts/           # 启动脚本
└── data/              # 输出数据
```

---

## 🌟 核心特性

- ✅ **两阶段生成**：LLM先规划主题，再生成样本
- ✅ **实时监控**：WebSocket推送进度和日志
- ✅ **多数据库**：支持MySQL、PostgreSQL、SQL Server
- ✅ **多格式**：Alpaca、ShareGPT格式输出
- ✅ **自动验证**：SQL语法和Schema验证
- ✅ **现代UI**：React + TypeScript + shadcn/ui

---

## 🆘 常见问题

### 后端启动失败？

```bash
# 检查依赖
pip install -r backend_requirements.txt

# 检查端口占用
lsof -i :8000
```

### 前端启动失败？

```bash
# 清除缓存重新安装
rm -rf node_modules package-lock.json
npm install
```

### 无法连接数据库？

- 检查数据库服务是否运行
- 验证用户名和密码
- 确认端口号正确

### LLM连接超时？

- 检查API地址和密钥
- 增加timeout设置
- 测试网络连接

---

## 📚 下一步

1. 阅读 [WEB_USAGE.md](WEB_USAGE.md) 了解Web界面详细使用
2. 查看 [API.md](API.md) 了解API接口
3. 参考 [README.md](README.md) 了解系统架构
4. 查看示例数据库 [example_database.sql](example_database.sql)

---

## 🎉 开始使用

现在您已经准备好开始使用了！

1. 启动服务：`./scripts/start_all.sh`
2. 打开浏览器：http://localhost:5173
3. 配置数据库和LLM
4. 开始生成训练数据

**祝您使用愉快！** 🚀

---

## 💬 技术支持

- 📖 查看文档
- 🐛 提交Issue
- 📧 联系维护者

**版本**: v1.0.0 | **更新**: 2024-11-03

