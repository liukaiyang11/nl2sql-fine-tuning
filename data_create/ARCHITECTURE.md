# 🏗️ 系统架构文档

## 📊 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户浏览器                              │
│                 (http://localhost:5173)                 │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │          React + TypeScript 前端              │  │
│  │                                               │  │
│  │  - 图片上传界面                               │  │
│  │  - 参数配置面板                               │  │
│  │  - 进度显示                                   │  │
│  │  - 结果下载                                   │  │
│  └──────────────────┬───────────────────────────┘  │
└─────────────────────┼───────────────────────────────┘
                      │
                      │ HTTP REST API
                      │
        ┌─────────────▼─────────────┐
        │   FastAPI 后端服务         │
        │ (http://localhost:8000)  │
        │                          │
        │  ┌────────────────────┐ │
        │  │   API路由层        │ │
        │  │  - /api/upload    │ │
        │  │  - /api/generate  │ │
        │  │  - /api/download  │ │
        │  └────────┬───────────┘ │
        │           │              │
        │  ┌────────▼───────────┐ │
        │  │   业务逻辑层        │ │
        │  │  - 文件处理        │ │
        │  │  - 数据生成        │ │
        │  └────────┬───────────┘ │
        └───────────┼──────────────┘
                    │
        ┌───────────▼──────────────┐
        │   外部API服务（可选）      │
        │                          │
        │  - OpenAI GPT-4 Vision   │
        │  - Claude 3              │
        │  - 通义千问 VL            │
        │  - 其他视觉模型           │
        └──────────────────────────┘
```

## 🔧 技术栈

### 前端 (Frontend)

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.3.1 | UI框架 |
| TypeScript | - | 类型安全 |
| Vite | 6.3.5 | 构建工具 |
| Tailwind CSS | - | 样式框架 |
| Radix UI | - | UI组件库 |
| Motion | - | 动画效果 |
| Lucide React | 0.487.0 | 图标库 |

### 后端 (Backend)

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.8+ | 运行环境 |
| FastAPI | 0.109.0 | Web框架 |
| Uvicorn | 0.27.0 | ASGI服务器 |
| httpx | 0.26.0 | HTTP客户端 |
| python-multipart | 0.0.6 | 文件上传 |

## 📁 目录结构详解

```
data_creat/
│
├── 📱 前端部分
│   ├── src/
│   │   ├── App.tsx                 # 主应用组件
│   │   ├── main.tsx               # 应用入口
│   │   ├── index.css              # 全局样式
│   │   └── components/            # UI组件库
│   │       ├── ui/                # shadcn/ui组件
│   │       └── figma/             # Figma组件
│   │
│   ├── public/                    # 静态资源
│   ├── package.json              # Node.js依赖配置
│   ├── vite.config.ts            # Vite配置
│   └── tsconfig.json             # TypeScript配置
│
├── ⚙️ 后端部分
│   └── backend/
│       ├── app.py                # 生产模式主程序
│       ├── demo_mode.py          # 演示模式程序
│       ├── requirements.txt      # Python依赖
│       ├── start.sh              # Linux/Mac启动脚本
│       ├── start.bat             # Windows启动脚本
│       ├── start_demo.sh         # 演示模式启动脚本
│       ├── start_demo.bat        # Windows演示模式启动
│       ├── uploads/              # 上传文件存储（运行时创建）
│       ├── outputs/              # 生成文件存储（运行时创建）
│       └── README.md             # 后端文档
│
└── 📖 文档部分
    ├── README.md                 # 主文档
    ├── QUICKSTART.md            # 快速开始
    └── ARCHITECTURE.md          # 架构文档（本文件）
```

## 🔄 数据流程

### 1. 图片上传流程

```
用户选择图片
    ↓
前端验证格式
    ↓
FormData封装
    ↓
POST /api/upload
    ↓
后端接收并验证
    ↓
生成唯一ID
    ↓
保存到uploads/
    ↓
返回文件信息
```

### 2. 数据生成流程

```
用户配置参数
    ↓
提交生成请求
    ↓
POST /api/generate
    ↓
遍历每张图片:
    ├─ 读取图片
    ├─ 转换为base64
    ├─ 调用视觉API
    ├─ 获取描述文本
    └─ 构建训练数据
    ↓
生成JSONL文件
    ↓
保存到outputs/
    ↓
返回结果统计
    ↓
前端自动下载
```

### 3. 文件下载流程

```
用户点击下载
    ↓
GET /api/download/{filename}
    ↓
后端验证文件存在
    ↓
返回文件流
    ↓
浏览器下载
```

## 🎯 核心模块说明

### 前端核心模块

#### App.tsx
主应用组件,包含:
- 状态管理 (useState)
- 文件上传逻辑
- API调用
- 进度追踪
- 用户交互

#### 组件系统
基于 shadcn/ui 的组件库:
- Button: 按钮组件
- Input: 输入框
- Select: 下拉选择
- Textarea: 文本域
- Slider: 滑块
- Progress: 进度条

### 后端核心模块

#### DataGenerator类
负责核心业务逻辑:

```python
class DataGenerator:
    async def call_vision_api()    # 调用视觉API
    def create_training_data()     # 生成训练数据格式
```

#### API路由

| 路由 | 方法 | 功能 |
|------|------|------|
| / | GET | 健康检查 |
| /api/upload | POST | 上传图片 |
| /api/generate | POST | 生成数据 |
| /api/download/{filename} | GET | 下载文件 |
| /api/outputs | GET | 列出所有输出 |
| /api/uploads/{filename} | DELETE | 删除上传文件 |

## 🔐 安全考虑

### 前端安全

1. **文件类型验证**
   ```typescript
   if (!file.type.startsWith('image/')) {
     // 拒绝非图片文件
   }
   ```

2. **CORS配置**
   - 限制允许的源
   - 仅在开发环境允许localhost

### 后端安全

1. **文件验证**
   ```python
   if not file.content_type.startswith("image/"):
       raise HTTPException(status_code=400)
   ```

2. **文件大小限制**
   - 默认限制100MB
   - 可通过配置调整

3. **路径安全**
   - 使用UUID生成文件名
   - 防止路径遍历攻击

4. **API密钥保护**
   - 不存储明文密钥
   - 仅在请求时传递

## 📈 性能优化

### 前端优化

1. **懒加载**
   - 组件按需加载
   - 代码分割

2. **状态管理**
   - 使用React Hooks
   - 避免不必要的重渲染

### 后端优化

1. **异步处理**
   ```python
   async def call_vision_api()  # 异步API调用
   ```

2. **并发控制**
   - 使用asyncio处理并发请求
   - 避免API速率限制

3. **文件流式传输**
   ```python
   return FileResponse()  # 流式返回大文件
   ```

## 🔄 扩展性设计

### 支持新的视觉模型

1. 在 `call_vision_api` 中添加新的API格式:

```python
if "new-model" in api_endpoint:
    payload = {
        # 新模型的请求格式
    }
```

2. 在前端Select组件中添加新选项:

```tsx
<SelectItem value="new-model">新模型</SelectItem>
```

### 自定义数据格式

修改 `create_training_data` 方法:

```python
def create_training_data(self, ...):
    return {
        # 你的自定义格式
    }
```

### 添加新功能

1. **前端**: 在App.tsx中添加新的UI和逻辑
2. **后端**: 在app.py中添加新的路由
3. **文档**: 更新README说明

## 🐛 调试建议

### 前端调试

1. 打开浏览器开发者工具
2. 查看Network标签的API请求
3. 查看Console标签的错误信息

### 后端调试

1. 查看终端输出日志
2. 访问 http://localhost:8000/docs 查看API文档
3. 使用Postman测试API端点

### 常见问题定位

| 问题 | 检查点 |
|------|--------|
| 上传失败 | 文件大小、格式、网络 |
| 生成失败 | API密钥、额度、网络 |
| 下载失败 | 文件是否存在、权限 |
| 连接失败 | 后端是否启动、端口 |

## 📝 开发建议

### 代码风格

- **前端**: 使用TypeScript严格模式
- **后端**: 遵循PEP 8规范
- **注释**: 使用中文注释说明关键逻辑

### 版本控制

```gitignore
# 不要提交
backend/uploads/
backend/outputs/
backend/venv/
.env
*.pyc
node_modules/
```

### 测试建议

1. 单元测试: 测试核心函数
2. 集成测试: 测试API端点
3. E2E测试: 测试完整流程

## 🚀 部署建议

### 开发环境
- 前端: Vite dev server
- 后端: Uvicorn reload模式

### 生产环境
- 前端: 静态文件部署(Nginx/CDN)
- 后端: Gunicorn + Uvicorn
- 反向代理: Nginx
- HTTPS: Let's Encrypt

---

最后更新: 2025-01-29

