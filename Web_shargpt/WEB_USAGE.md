# Web界面使用指南

## 🚀 快速启动

### 第一步：安装依赖

```bash
# 进入项目目录
cd Web_shargpt

# 安装后端Python依赖
pip install -r backend_requirements.txt

# 安装前端Node.js依赖
npm install
```

### 第二步：启动服务

**推荐方式：一键启动**
```bash
./scripts/start_all.sh
```

这会同时启动：
- 后端API服务器（端口8000）
- 前端开发服务器（端口5173）

**或者分别启动：**
```bash
# 终端1：启动后端
./scripts/start_backend.sh

# 终端2：启动前端  
./scripts/start_frontend.sh
```

### 第三步：访问界面

打开浏览器访问：`http://localhost:5173`

---

## 📋 界面功能说明

### 1. 数据库设置面板

填写数据库连接信息：

- **数据库类型**：选择MySQL、PostgreSQL或SQL Server
- **主机地址**：数据库服务器地址（如：localhost）
- **端口**：数据库端口（MySQL默认3306）
- **用户名**：数据库用户名
- **密码**：数据库密码
- **数据库名**：要分析的数据库名称

点击"**测试连接**"按钮验证配置是否正确。

### 2. 模型设置面板

配置LLM API信息：

- **API端点**：LLM服务地址（如：http://localhost:8000/v1）
- **模型名称**：模型名（如：qwen2.5-7b-instruct）
- **API密钥**：API访问密钥
- **Temperature**：控制生成随机性（0.3-0.5推荐，更稳定）
- **Top P**：核采样参数（0.9推荐）

点击"**测试连接**"按钮验证LLM配置。

### 3. 生成参数面板

设置生成选项：

- **SQL方言**：选择MySQL、PostgreSQL等
- **数据格式**：选择Alpaca或ShareGPT格式
- **样本数量**：要生成的训练样本数量（建议100-500）
- **输出路径**：输出文件路径（默认：./data/nl2sql.jsonl）
- **启用验证**：是否启用SQL语法验证（推荐开启）

### 4. 开始生成

配置完成后，点击"**开始生成**"按钮启动任务。

### 5. 进度监控

任务启动后，界面会实时显示：

- **当前步骤**：6个步骤的进度指示器
  1. 连接数据库
  2. 提取元数据  
  3. 生成表卡片
  4. 规划主题
  5. 生成SQL
  6. 验证结果

- **进度百分比**：当前任务完成进度
- **实时日志**：详细的执行日志输出

### 6. 查看结果

生成完成后：

1. 在日志中查看统计信息（总样本数、有效样本数）
2. 从`data/`目录获取输出文件：
   - `metadata.json` - 数据库元数据
   - `table_cards.json` - 表卡片
   - `plan.json` - 主题规划
   - `samples_raw.jsonl` - 原始样本
   - `samples_valid.jsonl` - 验证通过的样本
   - `nl2sql.jsonl` - 最终训练数据

---

## 💡 使用技巧

### 首次使用

1. **使用示例数据库**：
```bash
mysql -u root -p < example_database.sql
```

2. **测试配置**：
   - 数据库：localhost / 3306 / sales_demo
   - 样本数：先设置50条测试
   - 启用验证：建议开启

3. **观察日志**：实时查看每个步骤的执行情况

### 优化生成质量

1. **Temperature设置**：
   - 0.3-0.5：更稳定，适合生成可执行SQL
   - 0.7-0.9：更多样化，但可能需要更多验证

2. **样本数量**：
   - 测试：50-100条
   - 小型数据库：200-500条
   - 大型数据库：500-1000条

3. **验证选项**：
   - 开启验证：过滤无效SQL，质量更高
   - 关闭验证：生成更快，但需要人工审核

### 故障排查

**问题：数据库连接失败**
- 检查数据库服务是否运行
- 验证用户名、密码、端口
- 确认网络连接

**问题：LLM连接超时**
- 检查API地址是否正确
- 验证API密钥是否有效
- 检查网络连接
- 增加timeout值

**问题：生成的SQL不可执行**
- 降低temperature (0.3-0.5)
- 启用SQL验证
- 确保数据库表有注释
- 检查表结构是否完整

---

## 🔧 高级配置

### 自定义输出路径

在"生成参数"面板中修改输出路径：
- 相对路径：`./data/my_dataset.jsonl`
- 绝对路径：`/path/to/output/dataset.jsonl`

### 调整主题规划

生成的`data/plan.json`可以手动编辑：
- 修改主题名称
- 调整表选择
- 更改样本数量分配

编辑后，可以从命令行继续执行：
```bash
python auto_nl2sql.py --skip_planning
```

### 查看详细日志

所有日志保存在`logs/`目录：
```bash
# 查看最新日志
tail -f logs/auto_nl2sql_*.log

# 搜索错误
grep ERROR logs/auto_nl2sql_*.log
```

---

## 📊 生产部署

### 构建前端

```bash
./scripts/build_and_deploy.sh
```

这会将前端构建到`dist/`目录。

### 启动生产服务器

```bash
# 设置生产环境变量
export HOST=0.0.0.0
export PORT=8000

# 启动服务器
python app.py
```

访问：`http://your-server:8000`

### 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 📱 移动端访问

Web界面支持响应式设计，可以在移动设备上访问：

1. 确保移动设备与服务器在同一网络
2. 使用服务器IP地址访问：`http://192.168.x.x:5173`
3. 或配置域名访问

---

## 🆘 获取帮助

- **API文档**: http://localhost:8000/docs
- **详细说明**: [API.md](API.md)
- **常见问题**: [README.md](README.md)
- **快速开始**: [QUICKSTART.md](QUICKSTART.md)

---

**享受便捷的Web界面体验！** 🎉

