# NL2SQL数据生成系统 - API文档

## 概览

本系统提供REST API和WebSocket接口，用于控制NL2SQL数据生成任务和实时获取进度。

**基础URL**: `http://localhost:8000`

**API文档**: `http://localhost:8000/docs` (Swagger UI)

---

## REST API端点

### 1. 健康检查

**端点**: `GET /health`

**描述**: 检查API服务器状态

**响应示例**:
```json
{
  "status": "ok",
  "service": "nl2sql-api",
  "version": "1.0.0"
}
```

---

### 2. 测试数据库连接

**端点**: `POST /api/test-db-connection`

**描述**: 测试数据库连接是否正常

**请求体**:
```json
{
  "type": "mysql",
  "host": "localhost",
  "port": 3306,
  "user": "root",
  "password": "your_password",
  "database": "sales"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "数据库连接成功",
  "tables_count": 5
}
```

**错误响应**:
```json
{
  "detail": "数据库连接失败: Access denied for user..."
}
```

---

### 3. 测试LLM连接

**端点**: `POST /api/test-llm-connection`

**描述**: 测试LLM API连接是否正常

**请求体**:
```json
{
  "api_base": "http://localhost:8000/v1",
  "api_key": "sk-xxxx",
  "model_name": "qwen2.5-7b-instruct",
  "temperature": 0.7,
  "top_p": 0.9,
  "max_tokens": 4096,
  "timeout": 60,
  "max_retries": 3
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "LLM连接成功",
  "response": "连接成功"
}
```

---

### 4. 启动生成任务

**端点**: `POST /api/start-generation`

**描述**: 启动NL2SQL数据生成任务

**请求体**:
```json
{
  "db": {
    "type": "mysql",
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your_password",
    "database": "sales"
  },
  "llm": {
    "api_base": "http://localhost:8000/v1",
    "api_key": "sk-xxxx",
    "model_name": "qwen2.5-7b-instruct",
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 4096,
    "timeout": 60,
    "max_retries": 3
  },
  "generate": {
    "total_samples": 100,
    "dialect": "mysql",
    "output_path": "./data/nl2sql.jsonl",
    "output_format": "alpaca",
    "enable_validation": true,
    "min_tables_per_topic": 3,
    "max_tables_per_topic": 8
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "任务已启动"
}
```

**错误响应**:
```json
{
  "detail": "已有任务正在运行中"
}
```

---

### 5. 获取任务状态

**端点**: `GET /api/status`

**描述**: 获取当前任务的状态和进度

**响应示例**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "current_step": 3,
  "total_steps": 6,
  "step_name": "生成表卡片",
  "progress": 50,
  "error_message": "",
  "start_time": "2024-11-03T10:00:00.000000",
  "end_time": null,
  "details": {
    "config": {...},
    "samples_generated": 45,
    "samples_valid": 0
  }
}
```

**状态值**:
- `idle`: 空闲
- `running`: 运行中
- `completed`: 已完成
- `failed`: 失败
- `cancelled`: 已取消

---

### 6. 获取日志

**端点**: `GET /api/logs?limit=100`

**描述**: 获取任务执行日志

**查询参数**:
- `limit`: 返回的日志数量（默认100）

**响应示例**:
```json
{
  "logs": [
    {
      "type": "log",
      "level": "info",
      "message": "开始提取元数据...",
      "timestamp": "2024-11-03T10:00:00.000000"
    },
    {
      "type": "log",
      "level": "info",
      "message": "成功提取 5 个表的元数据",
      "timestamp": "2024-11-03T10:00:05.000000"
    }
  ]
}
```

---

### 7. 取消任务

**端点**: `POST /api/cancel`

**描述**: 取消当前正在运行的任务

**响应示例**:
```json
{
  "success": true,
  "message": "任务已取消"
}
```

---

## WebSocket接口

### 1. 实时日志推送

**端点**: `ws://localhost:8000/ws/logs`

**描述**: 接收实时日志消息

**消息格式**:
```json
{
  "type": "log",
  "level": "info",
  "message": "开始提取元数据...",
  "timestamp": "2024-11-03T10:00:00.000000"
}
```

**日志级别**:
- `debug`: 调试信息
- `info`: 普通信息
- `warning`: 警告信息
- `error`: 错误信息

---

### 2. 实时进度推送

**端点**: `ws://localhost:8000/ws/progress`

**描述**: 接收实时进度更新

**消息格式**:
```json
{
  "type": "progress",
  "step": 3,
  "total_steps": 6,
  "step_name": "生成表卡片",
  "progress": 50,
  "details": "正在生成表卡片摘要..."
}
```

---

### 3. 综合WebSocket

**端点**: `ws://localhost:8000/ws/all`

**描述**: 接收所有消息（日志+进度+状态）

**消息类型**:

1. **状态消息**:
```json
{
  "type": "status",
  "data": {
    "task_id": "...",
    "status": "running",
    ...
  }
}
```

2. **日志消息**:
```json
{
  "type": "log",
  "level": "info",
  "message": "...",
  "timestamp": "..."
}
```

3. **进度消息**:
```json
{
  "type": "progress",
  "step": 3,
  "total_steps": 6,
  "step_name": "...",
  "progress": 50,
  "details": "..."
}
```

**客户端命令**:

客户端可以发送以下命令到WebSocket:

- `ping`: 心跳检测，服务器会回复 `{"type": "pong"}`
- `get_status`: 获取当前状态
- `get_logs`: 获取历史日志

---

## 任务执行步骤

任务执行分为6个步骤：

1. **连接数据库** (Step 1)
   - 建立数据库连接
   - 验证连接有效性

2. **提取元数据** (Step 2)
   - 从information_schema提取表结构
   - 获取主外键关系

3. **生成表卡片** (Step 3)
   - 将元数据转换为简化格式
   - 生成表摘要

4. **规划主题** (Step 4, LLM阶段A)
   - 调用LLM分析表结构
   - 生成业务主题规划

5. **生成SQL样本** (Step 5, LLM阶段B)
   - 对每个主题生成NL+SQL样本
   - 基于DDL生成可执行SQL

6. **验证并导出** (Step 6)
   - 验证SQL语法和Schema
   - 导出为训练数据格式

---

## 使用示例

### Python示例

```python
import requests
import json

# 1. 测试数据库连接
db_config = {
    "type": "mysql",
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "sales"
}

response = requests.post("http://localhost:8000/api/test-db-connection", json=db_config)
print(response.json())

# 2. 启动生成任务
task_config = {
    "db": db_config,
    "llm": {
        "api_base": "http://localhost:8000/v1",
        "api_key": "sk-xxxx",
        "model_name": "qwen2.5-7b-instruct",
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 4096,
        "timeout": 60,
        "max_retries": 3
    },
    "generate": {
        "total_samples": 100,
        "dialect": "mysql",
        "output_path": "./data/nl2sql.jsonl",
        "output_format": "alpaca",
        "enable_validation": True
    }
}

response = requests.post("http://localhost:8000/api/start-generation", json=task_config)
print(response.json())

# 3. 获取状态
response = requests.get("http://localhost:8000/api/status")
print(response.json())
```

### JavaScript/TypeScript示例

```typescript
// 1. 测试数据库连接
const dbConfig = {
  type: "mysql",
  host: "localhost",
  port: 3306,
  user: "root",
  password: "123456",
  database: "sales"
};

const testResponse = await fetch("http://localhost:8000/api/test-db-connection", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(dbConfig)
});

console.log(await testResponse.json());

// 2. WebSocket连接
const ws = new WebSocket("ws://localhost:8000/ws/all");

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === "log") {
    console.log(`[${message.level}] ${message.message}`);
  } else if (message.type === "progress") {
    console.log(`进度: ${message.progress}% - ${message.step_name}`);
  } else if (message.type === "status") {
    console.log("状态更新:", message.data);
  }
};

ws.onopen = () => {
  console.log("WebSocket已连接");
  // 可以发送命令
  ws.send("get_status");
};
```

---

## 错误处理

所有API错误都返回标准的HTTP状态码和错误信息：

```json
{
  "detail": "错误描述信息"
}
```

**常见错误码**:
- `400`: 请求参数错误或业务逻辑错误
- `404`: 资源未找到
- `500`: 服务器内部错误

---

## 最佳实践

1. **连接测试**: 在启动任务前，先测试数据库和LLM连接
2. **WebSocket监控**: 使用WebSocket实时监控任务进度
3. **错误处理**: 妥善处理API返回的错误信息
4. **任务状态**: 定期轮询或监听任务状态
5. **资源清理**: 及时关闭不需要的WebSocket连接

---

## 更新日志

### v1.0.0 (2024-11-03)
- 初始版本
- 支持MySQL数据库
- 支持OpenAI兼容LLM API
- 支持Alpaca和ShareGPT输出格式
- 提供REST API和WebSocket接口
- 实时进度和日志推送

---

## 技术支持

如有问题，请查看：
- [README.md](README.md) - 系统使用文档
- [QUICKSTART.md](QUICKSTART.md) - 快速开始指南
- API文档: http://localhost:8000/docs

