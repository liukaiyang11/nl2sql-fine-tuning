# NL2SQL Fine-tuning

> 企业私有化 NL2SQL 模型微调实战，从数据构造、模型训练到推理部署全流程。

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![Transformers](https://img.shields.io/badge/Transformers-4.x+-yellow)](https://huggingface.co/docs/transformers/)
[![LoRA](https://img.shields.io/badge/LoRA-PEFT-green)](https://github.com/huggingface/peft)
[![vLLM](https://img.shields.io/badge/vLLM-0.4+-blueviolet)](https://github.com/vllm-project/vllm)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ 特性

- 🎯 **NL2SQL 微调**：将自然语言转为 SQL 查询的模型微调
- 📊 **数据构造工具**：自动生成 NL2SQL 训练数据
- 🔧 **LoRA 微调**：低秩适配，节省显存、加速训练
- ⚡ **vLLM 推理**：高性能推理部署
- 📈 **评测体系**：完整的准确率、执行率评测脚本
- 🌐 **Web 演示**：Web 界面实时测试效果

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────┐
│                    数据构造                          │
│  (SQL Schema + 业务语义 → NL2SQL 训练对)             │
└──────────────────┬──────────────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │   LoRA 微调训练    │
         │  (LLaMA-Factory)  │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │   评测 & 验证      │
         │  (准确率/执行率)   │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │   vLLM 推理部署    │
         │  (高吞吐在线服务)   │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │   Web 演示界面     │
         │  (Shargpt Demo)   │
         └───────────────────┘
```

---

## 📁 项目结构

```
.
├── train_lora.py             # LoRA 训练脚本
├── eval_model.py             # 模型评测脚本
├── vllm_test.py              # vLLM 推理测试
├── utils.py                  # 工具函数
├── requirements.txt
├── README.md
├── data_create/              # 数据构造工具
│   ├── backend/
│   └── frontend/
└── Web_shargpt/              # Web 演示界面
    ├── config.yaml
    └── ...
```

> 💡 **数据集**：Spider、CSpider 等 NL2SQL 数据集位于 `../data/datasets/`（约 3.7GB）。

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- CUDA 11.8+（GPU 训练推荐）
- 16GB+ 显存（7B 模型 LoRA 微调）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 数据准备

```bash
# 数据集位于 ../data/datasets/
# 也可使用 data_create/ 工具生成企业私有数据
cd data_create
# 参考内部文档使用数据构造工具
```

### LoRA 微调训练

```bash
python train_lora.py \
  --model_name_or_path qwen2.5-7b-instruct \
  --dataset ../data/datasets/spider_data \
  --finetuning_type lora \
  --output_dir output/nl2sql-lora \
  --num_train_epochs 3
```

### 模型评测

```bash
python eval_model.py \
  --model_name_or_path output/nl2sql-lora \
  --eval_dataset ../data/datasets/spider_data/dev.json
```

### vLLM 推理部署

```bash
python vllm_test.py \
  --model_name_or_path output/nl2sql-lora \
  --port 8000
```

---

## 📚 相关课程

- 📖 课程文档：[飞书知识库](#)（待补充）
- 🎥 视频教程：[课程链接](#)（待补充）

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
