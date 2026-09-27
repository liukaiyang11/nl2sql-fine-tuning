# 多模态微调数据生成器

一个强大的AI驱动的多模态微调数据生成工具，帮助你快速生成高质量的图像-文本对训练数据。

![预览图](./preview.png)

## ✨ 功能特性

- 🖼️ **批量图片上传** - 支持拖拽上传，一次处理多张图片
- 🤖 **AI自动标注** - 接入主流视觉大模型API（GPT-4 Vision、Claude 3、Gemini Pro、通义千问VL等）
- 📝 **灵活提示词** - 自定义系统提示词，控制标注风格和细节
- ⚙️ **参数可调** - 温度、模型选择等参数完全可控
- 📊 **实时进度** - 清晰的进度显示和成功/失败统计
- 💾 **JSONL格式** - 自动生成符合LLaMA-Factory等训练框架的JSONL格式数据
- 🎨 **现代UI** - 美观的渐变背景和动画效果

## 🚀 快速开始

### 前置要求

- Node.js 18+ 
- Python 3.8+
- 视觉模型API密钥（OpenAI、Claude、Gemini等）

### 安装步骤

#### 1. 克隆项目

```bash
cd data_creat
```

#### 2. 启动后端

```bash
# 进入后端目录
cd backend

# 方式1: 使用启动脚本（推荐）
# Linux/Mac
bash start.sh

# Windows
start.bat

# 方式2: 手动启动
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

后端服务将在 `http://localhost:8000` 启动

- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000

#### 3. 启动前端

```bash
# 在项目根目录（data_creat）
npm install
npm run dev
```

前端界面将在 `http://localhost:5173` 打开

## 📖 使用指南

### 基本流程

1. **上传图片**
   - 拖拽图片到上传区域，或点击上传按钮
   - 支持 JPG、PNG、WebP 格式

2. **配置模型**
   - 选择模型类型（GPT-4 Vision、Claude 3等）
   - 输入API接口地址
   - （可选）输入API密钥

3. **设置提示词**
   - 使用默认模板或自定义提示词
   - 调整温度参数（0.0-1.0）

4. **生成数据**
   - 点击"开始生成"按钮
   - 等待处理完成
   - 自动下载生成的JSONL文件

### 数据格式

生成的JSONL文件格式如下：

```json
{
  "messages": [
    {
      "role": "user",
      "content": "<image>请描述这张图片"
    },
    {
      "role": "assistant",
      "content": "这张图片展示了..."
    }
  ],
  "images": ["image_001.jpg"]
}
```

此格式兼容：
- LLaMA-Factory
- Qwen-VL训练框架
- 其他主流多模态训练工具

## 🔧 API接口配置

### OpenAI (GPT-4 Vision)

```
接口地址: https://api.openai.com/v1/chat/completions
模型: GPT-4 Vision
API Key: sk-...
```

### Claude 3 (Anthropic)

```
接口地址: https://api.anthropic.com/v1/messages
模型: Claude 3 Opus
API Key: sk-ant-...
```

### 通义千问VL (阿里云)

```
接口地址: https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation
模型: qwen-vl-plus
API Key: sk-...
```

### 自定义API

你可以配置任何兼容OpenAI接口格式的视觉模型API。

## 📁 项目结构

```
data_creat/
├── backend/                 # 后端API服务
│   ├── app.py              # FastAPI应用主文件
│   ├── requirements.txt    # Python依赖
│   ├── start.sh           # Linux/Mac启动脚本
│   ├── start.bat          # Windows启动脚本
│   ├── uploads/           # 上传的图片（自动创建）
│   └── outputs/           # 生成的JSONL文件（自动创建）
├── src/                    # 前端源码
│   ├── App.tsx            # 主应用组件
│   ├── components/        # UI组件库
│   └── styles/            # 样式文件
├── package.json           # Node.js配置
├── vite.config.ts         # Vite构建配置
└── README.md              # 本文档
```

## 🌐 API端点

后端提供以下REST API端点：

### 健康检查
```
GET /
返回: {"status": "ok", "message": "..."}
```

### 上传图片
```
POST /api/upload
Content-Type: multipart/form-data
Body: files (多个文件)
返回: {"success": true, "files": [...], "count": n}
```

### 生成数据
```
POST /api/generate
Content-Type: multipart/form-data
Body:
  - api_endpoint: 模型API地址
  - api_key: API密钥（可选）
  - system_prompt: 系统提示词
  - temperature: 温度参数
  - file_names: 文件名列表（JSON）
返回: {"success": n, "failed": m, "output_file": "..."}
```

### 下载文件
```
GET /api/download/{filename}
返回: JSONL文件
```

### 列出输出文件
```
GET /api/outputs
返回: {"files": [...]}
```

## 🎯 使用场景

- **多模态模型训练** - 为Qwen-VL、LLaVA等模型准备训练数据
- **图像数据集标注** - 批量为图像生成描述文本
- **数据增强** - 为现有数据集添加AI生成的标注
- **快速原型** - 快速测试不同的提示词策略

## ⚙️ 高级配置

### 自定义系统提示词模板

推荐的提示词模板：

```
你是一个专业的图像分析助手。请详细描述图片中的内容，包括：
1. 主要对象和场景
2. 颜色、光线、构图
3. 情感氛围和风格
4. 细节和特征
```

### 温度参数说明

- **0.0-0.3**: 更确定、一致的输出
- **0.4-0.7**: 平衡的创造性和准确性（推荐）
- **0.8-1.0**: 更有创造性和多样性的描述

## 🐛 故障排除

### 后端无法启动

1. 检查Python版本: `python --version` (需要3.8+)
2. 检查端口占用: `lsof -i:8000` (Mac/Linux) 或 `netstat -ano | findstr 8000` (Windows)
3. 查看日志输出了解具体错误

### 前端无法连接后端

1. 确保后端已启动在 `http://localhost:8000`
2. 检查浏览器控制台的CORS错误
3. 确认防火墙未阻止8000端口

### API调用失败

1. 验证API密钥是否正确
2. 检查API接口地址格式
3. 确认API余额充足
4. 查看后端日志获取详细错误信息

## 📝 数据格式说明

### 输入图片要求

- 格式: JPG, PNG, WebP
- 大小: 建议不超过10MB
- 分辨率: 建议不超过4096x4096

### 输出JSONL格式

每行一个JSON对象，包含：
- `messages`: 对话消息列表
- `images`: 图片文件名列表

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🔗 相关资源

- [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory)
- [Qwen-VL](https://github.com/QwenLM/Qwen-VL)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [React文档](https://react.dev/)

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- 提交GitHub Issue
- 发送邮件至项目维护者

---

Made with ❤️ for the AI community
