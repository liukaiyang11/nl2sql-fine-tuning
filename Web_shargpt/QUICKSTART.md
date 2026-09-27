# 快速开始指南

## 5分钟快速上手

### 步骤1：准备测试数据库

```bash
# 导入示例数据库
mysql -u root -p < example_database.sql

# 或者使用你自己的数据库
```

### 步骤2：安装依赖

```bash
pip install -r requirements.txt
```

### 步骤3：配置系统

编辑 `config.yaml`，修改以下关键配置：

```yaml
db:
  host: "127.0.0.1"      # 数据库地址
  port: 3306             # 数据库端口
  user: "root"           # 数据库用户名
  password: "your_pass"  # 数据库密码
  database: "sales_demo" # 数据库名称

llm:
  api_base: "http://127.0.0.1:8000/v1"  # LLM API地址
  api_key: "sk-xxxx"                     # LLM API密钥
  model_name: "qwen2.5-7b-instruct"      # 模型名称
```

### 步骤4：运行生成

```bash
# 首次测试：生成50条样本（约2-5分钟）
python auto_nl2sql.py --total_samples 50

# 正式使用：生成500条样本
python auto_nl2sql.py --total_samples 500
```

### 步骤5：查看结果

```bash
# 查看生成的训练数据
cat data/nl2sql.jsonl | head -n 3

# 查看统计信息（在日志中）
tail -n 50 logs/auto_nl2sql_*.log
```

## 常用命令

### 测试数据库连接

```python
# test_db.py
from modules.db_connector import create_connector
config = {
    'type': 'mysql',
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'your_password',
    'database': 'sales_demo'
}
conn = create_connector(config)
conn.get_connection()
print("数据库连接成功！")
```

### 测试LLM连接

```python
# test_llm.py
from modules.llm_client import create_llm_client
config = {
    'api_base': 'http://127.0.0.1:8000/v1',
    'api_key': 'sk-xxxx',
    'model_name': 'qwen2.5-7b-instruct',
    'temperature': 0.7,
    'top_p': 0.9,
    'max_tokens': 4096,
    'timeout': 60,
    'max_retries': 3
}
client = create_llm_client(config)
response = client.call_llm("你好，请说'连接成功'", expect_json=False)
print(response)
```

### 只生成元数据和规划（不调用LLM生成样本）

```python
# extract_only.py
import yaml
from modules.db_connector import create_connector
from modules.metadata_extractor import extract_and_save_metadata
from modules.table_cards import generate_and_save_table_cards

# 加载配置
with open('config.yaml') as f:
    config = yaml.safe_load(f)

# 连接数据库
db_conn = create_connector(config['db'])
db_conn.get_connection()

# 提取元数据
metadata = extract_and_save_metadata(db_conn, './data/metadata.json')

# 生成表卡片
cards = generate_and_save_table_cards(metadata, './data/table_cards.json')

print(f"提取了 {len(metadata)} 个表的元数据")
print(f"生成了 {len(cards)} 个表卡片")
```

## 输出格式示例

### Alpaca格式

```json
{
  "instruction": "根据以下数据库表结构，将自然语言问题转换为SQL查询语句。",
  "input": "查询所有北京用户的姓名和邮箱",
  "output": "SELECT name, email FROM users WHERE city = '北京';"
}
```

### ShareGPT格式

```json
{
  "conversations": [
    {"role": "user", "content": "查询所有北京用户的姓名和邮箱"},
    {"role": "assistant", "content": "SELECT name, email FROM users WHERE city = '北京';"}
  ]
}
```

## 用于LLaMA-Factory微调

### 1. 准备数据集信息

在LLaMA-Factory的 `data/dataset_info.json` 中添加：

```json
{
  "nl2sql_custom": {
    "file_name": "nl2sql.jsonl",
    "formatting": "alpaca",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output"
    }
  }
}
```

### 2. 运行微调

```bash
llamafactory-cli train \
  --stage sft \
  --model_name_or_path Qwen/Qwen2.5-7B-Instruct \
  --dataset nl2sql_custom \
  --template qwen \
  --finetuning_type lora \
  --output_dir ./output/nl2sql_lora \
  --per_device_train_batch_size 4 \
  --gradient_accumulation_steps 4 \
  --lr_scheduler_type cosine \
  --logging_steps 10 \
  --save_steps 100 \
  --learning_rate 5e-5 \
  --num_train_epochs 3.0 \
  --plot_loss \
  --fp16
```

## 故障排查

### 问题1：pymysql连接失败

```bash
# 检查MySQL是否运行
mysql -u root -p -e "SELECT 1;"

# 检查权限
GRANT ALL PRIVILEGES ON sales_demo.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
```

### 问题2：LLM返回格式错误

修改config.yaml：

```yaml
llm:
  temperature: 0.3  # 降低温度，提高稳定性
  max_retries: 5    # 增加重试次数
```

### 问题3：生成样本太慢

```bash
# 方法1：减少样本数
python auto_nl2sql.py --total_samples 100

# 方法2：跳过验证
python auto_nl2sql.py --skip_validation

# 方法3：使用更快的模型
# 在config.yaml中修改model_name为小模型
```

## 进阶使用

### 自定义Prompt模板

修改 `modules/generator.py` 中的 `_build_generation_prompt` 方法。

### 增加新的数据库类型

修改 `modules/db_connector.py`，添加新的数据库驱动。

### 自定义验证规则

修改 `modules/validator.py`，添加自定义验证逻辑。

## 下一步

- 📖 阅读完整文档：[README.md](README.md)
- 🔧 查看配置说明：[config.yaml](config.yaml)
- 📊 分析生成数据质量
- 🚀 使用LLaMA-Factory进行模型微调

---

有问题？查看 [README.md](README.md) 或提交Issue！

