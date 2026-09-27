# 🚀 快速开始指南

5分钟快速上手多模态微调数据生成器！

## 📋 前置条件

- ✅ 已安装 Node.js 18+
- ✅ 已安装 Python 3.8+
- 📝 准备好一些测试图片

## 🎯 步骤1: 启动后端（演示模式）

无需任何API密钥，立即体验！

### Mac/Linux
```bash
cd backend
bash start.sh
# 当看到 "Application startup complete" 时，后端已就绪
```

### Windows
```bash
cd backend
start.bat
# 当看到 "Application startup complete" 时，后端已就绪
```

💡 **提示**: 首次运行会自动安装依赖，需要等待1-2分钟

## 🎯 步骤2: 启动前端

打开新的终端窗口：

```bash
# 在项目根目录（data_creat）
npm install
npm run dev

npm install 过慢的情况下(参考)：
方法1：临时使用淘宝镜像（最快）
# 使用淘宝镜像安装
npm install --registry=https://registry.npmmirror.com
方法2：永久配置淘宝镜像
# 配置 npm 使用淘宝镜像
npm config set registry https://registry.npmmirror.com

# 验证配置
npm config get registry

# 然后正常安装
npm install
方法3：使用 cnpm（备选）
# 安装 cnpm
npm install -g cnpm --registry=https://registry.npmmirror.com

# 使用 cnpm 安装
cnpm install
方法4：使用 pnpm（推荐，更快）
# 安装 pnpm
npm install -g pnpm --registry=https://registry.npmmirror.com

# 配置镜像
pnpm config set registry https://registry.npmmirror.com
# 安装依赖
pnpm install
# 运行
pnpm run dev
```

等待编译完成后，浏览器会自动打开 `http://localhost:5173`

## 🎯 步骤3: 生成你的第一批数据

1. **上传图片**
   - 拖拽几张图片到上传区域
   - 或点击上传按钮选择文件

2. **配置（可以使用默认值）**
   - API接口地址: 随便填写（演示模式不会真实调用）
   - 点击"使用默认模板"按钮

3. **开始生成**
   - 点击"开始生成"按钮
   - 等待处理完成（每张图片约0.5秒）
   - 自动下载生成的JSONL文件

## ✨ 恭喜！

你已经成功生成了第一批训练数据！

生成的文件格式：
```json
{"messages": [...], "images": ["xxx.jpg"]}
{"messages": [...], "images": ["yyy.jpg"]}
```

## 🔄 下一步：使用真实API

### 1. 获取API密钥

选择一个视觉模型服务：
- [OpenAI GPT-4 Vision](https://platform.openai.com/)
- [Claude 3](https://www.anthropic.com/)
- [通义千问VL](https://dashscope.console.aliyun.com/)

### 2. 切换到生产模式

修改 `backend/start.sh`（或 `start.bat`）:

```bash
# 将最后一行改为
python app.py  # 替代 python demo_mode.py
```

### 3. 配置API信息

在前端界面中输入：
- ✏️ API接口地址（参考README中的配置）
- 🔑 你的API密钥
- 📝 自定义系统提示词

### 4. 开始真实标注

点击"开始生成"，AI将为你的图片生成真实的描述！

## 💡 常见问题

### Q: 演示模式生成的数据能用吗？
A: 演示模式生成的是模拟数据，仅用于测试流程。真实训练需使用生产模式。

### Q: 支持哪些图片格式？
A: JPG、PNG、WebP，建议单张不超过10MB

### Q: 如何批量处理大量图片？
A: 一次可上传多张图片，建议每批不超过50张以保证稳定性

### Q: 生成的数据保存在哪里？
A: 后端服务器的 `backend/outputs/` 目录，同时会自动下载到你的电脑

### Q: 可以自定义数据格式吗？
A: 可以！修改 `backend/app.py` 中的 `create_training_data` 方法

## 📚 进阶使用

准备好深入了解？查看完整文档：

- 📖 [完整README](./README.md)
- 🔧 [后端API文档](./backend/README.md)
- 🌐 [API接口文档](http://localhost:8000/docs) (启动后端后访问)

## 🆘 需要帮助？

- 💬 提交 [GitHub Issue](../../issues)
- 📧 查看项目文档
- 🔍 搜索常见问题

---

祝你使用愉快！🎉

