"""
LoRA 微调脚本
支持 DeepSeek Coder 模型的 LoRA 微调，包含早停机制
"""

import os
import argparse
import json
from typing import Dict, List
import torch

# 设置环境变量，避免tokenizers的fork警告
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
    TrainerCallback,
    TrainerState,
    TrainerControl
)
from peft import (
    LoraConfig,
    get_peft_model,
    TaskType,
    PeftModel
)
from datasets import Dataset
import numpy as np
from tqdm import tqdm

from utils import load_data, build_prompt


class EarlyStoppingCallback:
    """早停回调类"""
    
    def __init__(self, patience: int = 3, min_delta: float = 0.0):
        """
        Args:
            patience: 容忍的验证集loss不下降的epoch数
            min_delta: 最小改善幅度
        """
        self.patience = patience
        self.min_delta = min_delta
        self.best_loss = float('inf')
        self.counter = 0
        self.should_stop = False
    
    def check(self, current_loss: float, model, save_path: str) -> bool:
        """
        检查是否应该早停
        
        Args:
            current_loss: 当前验证集loss
            model: 模型对象
            save_path: 模型保存路径
        
        Returns:
            是否应该停止训练
        """
        if current_loss < self.best_loss - self.min_delta:
            # Loss 下降，更新最佳值
            self.best_loss = current_loss
            self.counter = 0
            
            # 保存最佳模型
            print(f"💾 验证集 Loss 改善: {current_loss:.4f}, 保存模型到 {save_path}")
            model.save_pretrained(save_path)
            
            return False
        else:
            # Loss 没有改善
            self.counter += 1
            print(f"⚠️  验证集 Loss 未改善 ({self.counter}/{self.patience}): {current_loss:.4f} (最佳: {self.best_loss:.4f})")
            
            if self.counter >= self.patience:
                print(f"🛑 早停触发！连续 {self.patience} 个 epoch 验证集 Loss 未改善")
                self.should_stop = True
                return True
            
            return False


def prepare_dataset(
    data_path: str,
    tokenizer,
    max_length: int = 2048,
    data_format: str = "auto"
) -> Dataset:
    """
    准备训练/验证数据集
    
    Args:
        data_path: 数据文件路径
        tokenizer: 分词器
        max_length: 最大序列长度
        data_format: 数据格式 ("alpaca", "sharegpt", "auto")
    
    Returns:
        处理后的 Dataset
    """
    print(f"📂 加载数据: {data_path}")
    
    # 加载数据
    data = load_data(data_path, data_format=data_format)
    print(f"✅ 加载了 {len(data)} 条数据")
    
    # 准备训练样本
    samples = []
    for item in tqdm(data, desc="处理数据"):
        question = item['question']
        sql = item['sql']
        
        # 构建 Prompt
        prompt = build_prompt(question, is_training=True, sql=sql)
        
        # Tokenize
        tokenized = tokenizer(
            prompt,
            truncation=True,
            max_length=max_length,
            padding=False,
            return_tensors=None
        )
        
        # 设置 labels（用于计算loss）
        tokenized['labels'] = tokenized['input_ids'].copy()
        
        samples.append(tokenized)
    
    # 转换为 Dataset
    dataset = Dataset.from_list(samples)
    
    print(f"✅ 数据集准备完成，共 {len(dataset)} 条样本")
    
    return dataset


def evaluate_model(model, tokenizer, val_dataset, device) -> float:
    """
    在验证集上评估模型
    
    Args:
        model: 模型
        tokenizer: 分词器
        val_dataset: 验证数据集
        device: 设备
    
    Returns:
        平均 loss
    """
    model.eval()
    total_loss = 0.0
    num_samples = 0
    
    with torch.no_grad():
        for i in tqdm(range(len(val_dataset)), desc="验证中"):
            sample = val_dataset[i]
            
            # 准备输入
            input_ids = torch.tensor([sample['input_ids']]).to(device)
            attention_mask = torch.tensor([sample['attention_mask']]).to(device)
            labels = torch.tensor([sample['labels']]).to(device)
            
            # 前向传播
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            
            loss = outputs.loss
            total_loss += loss.item()
            num_samples += 1
    
    avg_loss = total_loss / num_samples if num_samples > 0 else 0.0
    model.train()
    
    return avg_loss


def train(
    model_path: str,
    train_data: str,
    val_data: str,
    output_dir: str,
    num_epochs: int = 10,
    batch_size: int = 8,
    gradient_accumulation_steps: int = 4,
    learning_rate: float = 2e-4,
    lora_rank: int = 16,
    lora_alpha: int = 32,
    lora_dropout: float = 0.05,
    max_length: int = 2048,
    early_stopping_patience: int = 3,
    data_format: str = "auto",
    save_steps: int = 500,
    logging_steps: int = 10,
    warmup_ratio: float = 0.05
):
    """
    执行 LoRA 微调
    
    Args:
        model_path: 基座模型路径
        train_data: 训练数据路径
        val_data: 验证数据路径
        output_dir: 输出目录
        num_epochs: 训练轮数
        batch_size: 批次大小
        gradient_accumulation_steps: 梯度累积步数
        learning_rate: 学习率
        lora_rank: LoRA rank
        lora_alpha: LoRA alpha
        lora_dropout: LoRA dropout
        max_length: 最大序列长度
        early_stopping_patience: 早停容忍度
        data_format: 数据格式
        save_steps: 保存步数
        logging_steps: 日志步数
        warmup_ratio: warmup 比例
    """
    print("=" * 80)
    print("🚀 开始 LoRA 微调训练")
    print("=" * 80)
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    best_model_path = os.path.join(output_dir, "best_model")
    os.makedirs(best_model_path, exist_ok=True)
    
    # 1. 加载分词器和模型
    print(f"\n📥 加载模型: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
        padding_side='right'
    )
    
    # 设置 pad_token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        trust_remote_code=True,
        dtype=torch.float16,
        device_map="auto"
    )
    
    print(f"✅ 模型加载完成")
    print(f"📊 模型参数量: {model.num_parameters() / 1e9:.2f}B")
    
    # 2. 配置 LoRA
    print(f"\n⚙️  配置 LoRA (rank={lora_rank}, alpha={lora_alpha})")
    
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=lora_rank,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none"
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # 启用输入梯度（gradient checkpointing需要）
    # 使用更强的方法确保梯度能够正确传播
    if hasattr(model, "enable_input_require_grads"):
    model.enable_input_require_grads()
    else:
        def make_inputs_require_grad(module, input, output):
            output.requires_grad_(True)
        model.get_input_embeddings().register_forward_hook(make_inputs_require_grad)
    
    # 额外确保：为embedding层启用梯度
    for param in model.get_input_embeddings().parameters():
        param.requires_grad = True
    
    # 3. 准备数据集
    print("\n📊 准备数据集...")
    train_dataset = prepare_dataset(train_data, tokenizer, max_length, data_format)
    val_dataset = prepare_dataset(val_data, tokenizer, max_length, data_format)
    
    # 4. 配置训练参数
    print("\n⚙️  配置训练参数...")
    # 注意：这里设置 num_train_epochs=1，因为我们在外层循环中控制epoch
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=1,  # 每次只训练1个epoch
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=learning_rate,
        warmup_ratio=warmup_ratio,
        logging_steps=logging_steps,
        save_steps=save_steps,
        save_total_limit=2,
        fp16=True,
        gradient_checkpointing=True,
        max_grad_norm=0.0,  # 禁用梯度裁剪，避免fp16的unscale错误
        dataloader_num_workers=4,
        remove_unused_columns=False,
        report_to="none",
        load_best_model_at_end=False,
    )
    
    print(f"✅ 训练配置:")
    print(f"   - Epochs: {num_epochs}")
    print(f"   - Batch size: {batch_size}")
    print(f"   - Gradient accumulation: {gradient_accumulation_steps}")
    print(f"   - Effective batch size: {batch_size * gradient_accumulation_steps}")
    print(f"   - Learning rate: {learning_rate}")
    print(f"   - Max length: {max_length}")
    
    # 5. 数据处理器
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        padding=True,
        return_tensors="pt",
        label_pad_token_id=-100  # 确保labels正确padding
    )
    
    # 6. 训练循环（带早停）
    print("\n" + "=" * 80)
    print("🏋️  开始训练（带早停机制）")
    print("=" * 80)
    
    early_stopping = EarlyStoppingCallback(patience=early_stopping_patience)
    device = next(model.parameters()).device
    
    for epoch in range(num_epochs):
        print(f"\n{'='*80}")
        print(f"📅 Epoch {epoch + 1}/{num_epochs}")
        print(f"{'='*80}")
        
        # 每个epoch重新创建trainer以避免状态问题
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            data_collator=data_collator,
        )
        
        # 训练一个 epoch
        trainer.train()
        
        # 保存当前 epoch 的检查点
        epoch_save_path = os.path.join(output_dir, f"checkpoint-epoch-{epoch+1}")
        model.save_pretrained(epoch_save_path)
        print(f"💾 保存 Epoch {epoch+1} 检查点到: {epoch_save_path}")
        
        # 在验证集上评估
        print(f"\n📊 在验证集上评估...")
        val_loss = evaluate_model(model, tokenizer, val_dataset, device)
        print(f"📈 验证集 Loss: {val_loss:.4f}")
        
        # 检查早停
        should_stop = early_stopping.check(val_loss, model, best_model_path)
        
        if should_stop:
            print(f"\n✅ 训练完成（早停触发）")
            break
    
    else:
        # 正常完成所有 epochs
        print(f"\n✅ 训练完成（完成所有 {num_epochs} 个 epochs）")
    
    # 7. 保存最终模型和训练配置
    print(f"\n💾 保存最终配置...")
    
    # 保存分词器
    tokenizer.save_pretrained(best_model_path)
    
    # 保存训练配置
    config_info = {
        "model_path": model_path,
        "lora_rank": lora_rank,
        "lora_alpha": lora_alpha,
        "learning_rate": learning_rate,
        "batch_size": batch_size,
        "num_epochs": num_epochs,
        "best_val_loss": early_stopping.best_loss,
        "data_format": data_format
    }
    
    with open(os.path.join(output_dir, "training_config.json"), 'w', encoding='utf-8') as f:
        json.dump(config_info, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 训练完成！")
    print(f"📁 最佳模型保存在: {best_model_path}")
    print(f"📊 最佳验证集 Loss: {early_stopping.best_loss:.4f}")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="NL2SQL LoRA 微调脚本")
    
    # 模型和数据参数
    parser.add_argument("--model_path", type=str, required=True, help="基座模型路径")
    parser.add_argument("--train_data", type=str, required=True, help="训练数据路径")
    parser.add_argument("--val_data", type=str, required=True, help="验证数据路径")
    parser.add_argument("--output_dir", type=str, default="./output", help="输出目录")
    parser.add_argument("--data_format", type=str, default="auto", 
                       choices=["auto", "alpaca", "sharegpt"], help="数据格式")
    
    # 训练参数
    parser.add_argument("--num_epochs", type=int, default=10, help="训练轮数")
    parser.add_argument("--batch_size", type=int, default=8, help="批次大小")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=4, help="梯度累积步数")
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="学习率")
    parser.add_argument("--warmup_ratio", type=float, default=0.05, help="Warmup 比例")
    parser.add_argument("--max_length", type=int, default=2048, help="最大序列长度")
    
    # LoRA 参数
    parser.add_argument("--lora_rank", type=int, default=16, help="LoRA rank")
    parser.add_argument("--lora_alpha", type=int, default=32, help="LoRA alpha")
    parser.add_argument("--lora_dropout", type=float, default=0.05, help="LoRA dropout")
    
    # 早停参数
    parser.add_argument("--early_stopping_patience", type=int, default=3, 
                       help="早停容忍度（连续多少个epoch验证集loss不下降）")
    
    # 其他参数
    parser.add_argument("--save_steps", type=int, default=500, help="保存步数")
    parser.add_argument("--logging_steps", type=int, default=10, help="日志步数")
    
    args = parser.parse_args()
    
    # 执行训练
    train(
        model_path=args.model_path,
        train_data=args.train_data,
        val_data=args.val_data,
        output_dir=args.output_dir,
        num_epochs=args.num_epochs,
        batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        lora_rank=args.lora_rank,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        max_length=args.max_length,
        early_stopping_patience=args.early_stopping_patience,
        data_format=args.data_format,
        save_steps=args.save_steps,
        logging_steps=args.logging_steps,
        warmup_ratio=args.warmup_ratio
    )


if __name__ == "__main__":
    main()
