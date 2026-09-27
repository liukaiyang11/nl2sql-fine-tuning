"""
模型评估脚本
支持文本匹配和SQL执行双重验证
"""

import os
import argparse
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from tqdm import tqdm
from typing import List, Dict, Tuple
from utils import (
    load_data,
    build_prompt,
    SQLExecutor,
    calculate_exact_match,
    calculate_average_f1,
    extract_sql_from_output,
    normalize_sql
)


class ModelEvaluator:
    """模型评估器"""
    
    def __init__(
        self,
        model_path: str,
        lora_path: str = None,
        device: str = "cuda"
    ):
        """
        初始化评估器
        
        Args:
            model_path: 基础模型路径
            lora_path: LoRA权重路径（可选）
            device: 设备
        """
        self.device = device
        print(f"\n{'='*50}")
        print("正在加载模型...")
        print(f"{'='*50}")
        
        # 加载分词器
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        
        print(f"✓ 分词器加载完成")
        
        # 加载基础模型
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map='auto'
        )
        
        print(f"✓ 基础模型加载完成")
        
        # 如果提供了LoRA路径，加载LoRA权重
        if lora_path:
            self.model = PeftModel.from_pretrained(
                self.model,
                lora_path,
                torch_dtype=torch.float16
            )
            print(f"✓ LoRA权重加载完成: {lora_path}")
        
        self.model.eval()
        print(f"✓ 模型已设置为评估模式")
    
    def generate_sql(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.1,
        top_p: float = 0.95
    ) -> str:
        """
        生成SQL查询
        
        Args:
            prompt: 输入prompt
            max_new_tokens: 最大生成token数
            temperature: 温度参数
            top_p: top_p采样参数
        
        Returns:
            生成的SQL查询
        """
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # 解码生成的文本
        generated_text = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        
        # 提取SQL
        sql = extract_sql_from_output(generated_text)
        return sql
    
    def generate_sql_batch(
        self,
        prompts: List[str],
        max_new_tokens: int = 512,
        temperature: float = 0.1,
        top_p: float = 0.95
    ) -> List[str]:
        """
        批量生成SQL（提高显卡利用率）
        
        Args:
            prompts: prompt列表
            max_new_tokens: 最大生成token数
            temperature: 生成温度
            top_p: top_p采样参数
        
        Returns:
            生成的SQL查询列表
        """
        # Tokenize所有prompts
        inputs = self.tokenizer(
            prompts,
            return_tensors="pt",
            truncation=True,
            max_length=2048,
            padding=True
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # 解码所有生成的文本
        sqls = []
        for i, output in enumerate(outputs):
            generated_text = self.tokenizer.decode(
                output[inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            )
            sql = extract_sql_from_output(generated_text)
            sqls.append(sql)
        
        return sqls
    
    def evaluate_text_match(
        self,
        test_data: List[Dict],
        batch_size: int = 8,
        output_file: str = None
    ) -> Dict[str, float]:
        """
        评估文本匹配准确率
        
        Args:
            test_data: 测试数据
            batch_size: 批量推理大小
            output_file: 输出文件路径（可选）
        
        Returns:
            评估指标字典
        """
        print(f"\n{'='*50}")
        print("开始文本匹配评估")
        print(f"{'='*50}\n")
        print(f"批量大小: {batch_size}")
        
        predictions = []
        references = []
        results = []
        
        # 批量处理
        for i in tqdm(range(0, len(test_data), batch_size), desc="生成SQL"):
            batch = test_data[i:i+batch_size]
            
            # 准备批量数据
            batch_prompts = []
            batch_references = []
            
            for item in batch:
                question = item.get('question', '')
                reference_sql = item.get('sql', '')
                prompt = build_prompt(question, is_training=False)
                
                batch_prompts.append(prompt)
                batch_references.append(reference_sql)
            
            # 批量生成SQL
            batch_predictions = self.generate_sql_batch(batch_prompts)
            
            predictions.extend(batch_predictions)
            references.extend(batch_references)
            
            # 记录详细结果
            for prompt, ref_sql, pred_sql in zip(batch_prompts, batch_references, batch_predictions):
                results.append({
                    'prompt': prompt.strip(),
                    'reference': ref_sql.strip(),
                    'prediction': pred_sql.strip(),
                    'exact_match': normalize_sql(pred_sql) == normalize_sql(ref_sql)
                })
        
        # 计算指标
        exact_match_acc = calculate_exact_match(predictions, references)
        avg_f1 = calculate_average_f1(predictions, references)
        
        metrics = {
            'exact_match': exact_match_acc,
            'token_f1': avg_f1,
            'total_samples': len(test_data)
        }
        
        print(f"\n文本匹配评估结果:")
        print(f"  样本总数: {metrics['total_samples']}")
        print(f"  精确匹配准确率: {metrics['exact_match']:.2%}")
        print(f"  Token级F1分数: {metrics['token_f1']:.4f}")
        
        # 保存详细结果
        if output_file:
            output_data = {
                'metrics': metrics,
                'results': results
            }
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"\n✓ 详细结果已保存到: {output_file}")
        
        return metrics
    
    def evaluate_sql_execution(
        self,
        test_data: List[Dict],
        db_executor: SQLExecutor,
        batch_size: int = 8,
        output_file: str = None
    ) -> Dict[str, float]:
        """
        评估SQL执行准确率
        
        Args:
            test_data: 测试数据
            db_executor: 数据库执行器
            batch_size: 批量推理大小
            output_file: 输出文件路径（可选）
        
        Returns:
            评估指标字典
        """
        print(f"\n{'='*50}")
        print("开始SQL执行评估")
        print(f"{'='*50}\n")
        print(f"批量大小: {batch_size}")
        
        # 第一步：批量生成所有SQL（加速推理）
        print("\n[步骤1/2] 批量生成SQL...")
        all_predictions = []
        all_references = []
        all_prompts = []
        
        for i in tqdm(range(0, len(test_data), batch_size), desc="生成SQL"):
            batch = test_data[i:i+batch_size]
            
            batch_prompts = []
            batch_references = []
            
            for item in batch:
                question = item.get('question', '')
                reference_sql = item.get('sql', '')
                prompt = build_prompt(question, is_training=False)
                
                batch_prompts.append(prompt)
                batch_references.append(reference_sql)
            
            # 批量生成SQL
            batch_predictions = self.generate_sql_batch(batch_prompts)
            
            all_predictions.extend(batch_predictions)
            all_references.extend(batch_references)
            all_prompts.extend(batch_prompts)
        
        # 第二步：执行SQL并验证结果
        print("\n[步骤2/2] 执行SQL并验证...")
        
        # 打印前3个SQL样本用于调试
        print("\n样本预览（前3个）：")
        for i in range(min(3, len(all_predictions))):
            print(f"\n样本 {i+1}:")
            print(f"  问题: {test_data[i].get('question', '')[:60]}...")
            print(f"  参考SQL: {all_references[i][:80]}...")
            print(f"  预测SQL: {all_predictions[i][:80]}...")
        print()
        
        total_samples = 0
        execution_success = 0
        result_match = 0
        reference_exec_success = 0
        results = []
        
        for idx, (prompt, reference_sql, predicted_sql) in enumerate(
            tqdm(zip(all_prompts, all_references, all_predictions), 
                 total=len(all_predictions), 
                 desc="执行SQL")
        ):
            
            # 执行参考SQL
            ref_success, reference_result = db_executor.execute_sql(reference_sql)
            if ref_success:
                reference_exec_success += 1
            
            # 执行预测SQL
            pred_success, predicted_result = db_executor.execute_sql(predicted_sql)
            if pred_success:
                execution_success += 1
            
            # 比较结果
            is_match = False
            if ref_success and pred_success:
                # 直接比较结果
                is_match = (reference_result == predicted_result)
                if is_match:
                    result_match += 1
            
            total_samples += 1
            
            # 记录详细结果（包含错误信息）
            result_detail = {
                'prompt': prompt.strip(),
                'reference_sql': reference_sql.strip(),
                'predicted_sql': predicted_sql.strip(),
                'reference_executed': ref_success,
                'prediction_executed': pred_success,
                'results_match': is_match,
            }
            
            # 添加执行结果或错误信息
            if ref_success:
                result_detail['reference_result_count'] = len(reference_result) if isinstance(reference_result, (list, tuple)) else 0
            else:
                result_detail['reference_error'] = str(reference_result)
            
            if pred_success:
                result_detail['predicted_result_count'] = len(predicted_result) if isinstance(predicted_result, (list, tuple)) else 0
            else:
                result_detail['prediction_error'] = str(predicted_result)
            
            results.append(result_detail)
        
        # 计算指标
        metrics = {
            'total_samples': total_samples,
            'reference_execution_rate': reference_exec_success / total_samples if total_samples > 0 else 0,
            'prediction_execution_rate': execution_success / total_samples if total_samples > 0 else 0,
            'execution_match_rate': result_match / total_samples if total_samples > 0 else 0,
            'execution_match_rate_of_valid': result_match / reference_exec_success if reference_exec_success > 0 else 0
        }
        
        print(f"\nSQL执行评估结果:")
        print(f"  样本总数: {metrics['total_samples']}")
        print(f"  参考SQL执行成功率: {metrics['reference_execution_rate']:.2%}")
        print(f"  预测SQL执行成功率: {metrics['prediction_execution_rate']:.2%}")
        print(f"  结果匹配率（全部样本）: {metrics['execution_match_rate']:.2%}")
        print(f"  结果匹配率（有效样本）: {metrics['execution_match_rate_of_valid']:.2%}")
        
        # 如果执行失败，显示前几个错误
        if reference_exec_success == 0:
            print(f"\n⚠️  警告：所有参考SQL都执行失败！显示前3个错误：")
            for i, result in enumerate(results[:3]):
                if not result['reference_executed']:
                    print(f"\n样本 {i+1}:")
                    print(f"  SQL: {result['reference_sql'][:80]}...")
                    print(f"  错误: {result.get('reference_error', 'Unknown error')}")
        
        if execution_success == 0:
            print(f"\n⚠️  警告：所有预测SQL都执行失败！显示前3个错误：")
            for i, result in enumerate(results[:3]):
                if not result['prediction_executed']:
                    print(f"\n样本 {i+1}:")
                    print(f"  SQL: {result['predicted_sql'][:80]}...")
                    print(f"  错误: {result.get('prediction_error', 'Unknown error')}")
        
        # 保存详细结果
        if output_file:
            output_data = {
                'metrics': metrics,
                'results': results
            }
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"\n✓ 详细结果已保存到: {output_file}")
        
        return metrics


def main():
    parser = argparse.ArgumentParser(description="NL2SQL模型评估")
    
    # 模型参数
    parser.add_argument("--model_path", type=str, required=True,
                        help="基础模型路径")
    parser.add_argument("--lora_path", type=str, default=None,
                        help="LoRA权重路径（可选）")
    
    # 数据参数
    parser.add_argument("--test_data", type=str, required=True,
                        help="测试数据路径")
    parser.add_argument("--output_dir", type=str, default="./eval_results",
                        help="评估结果输出目录")
    
    # 数据库参数
    parser.add_argument("--db_host", type=str, default=None,
                        help="数据库主机地址")
    parser.add_argument("--db_port", type=int, default=3306,
                        help="数据库端口")
    parser.add_argument("--db_user", type=str, default="root",
                        help="数据库用户名")
    parser.add_argument("--db_password", type=str, default="",
                        help="数据库密码")
    parser.add_argument("--db_name", type=str, default="",
                        help="数据库名称")
    
    # 评估参数
    parser.add_argument("--eval_text_match", action="store_true", default=True,
                        help="是否评估文本匹配")
    parser.add_argument("--eval_sql_execution", action="store_true",
                        help="是否评估SQL执行")
    parser.add_argument("--max_samples", type=int, default=None,
                        help="最大评估样本数（用于快速测试）")
    parser.add_argument("--batch_size", type=int, default=8,
                        help="批量推理大小（增加可提高显卡利用率，默认8）")
    
    # 生成参数
    parser.add_argument("--max_new_tokens", type=int, default=512,
                        help="最大生成token数")
    parser.add_argument("--temperature", type=float, default=0.1,
                        help="生成温度")
    parser.add_argument("--top_p", type=float, default=0.95,
                        help="top_p采样参数")
    
    args = parser.parse_args()
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 加载测试数据
    print(f"\n{'='*50}")
    print("正在加载测试数据...")
    print(f"{'='*50}")
    
    test_data = load_data(args.test_data)
    
    if args.max_samples:
        test_data = test_data[:args.max_samples]
        print(f"✓ 使用前{args.max_samples}个样本进行评估")
    else:
        print(f"✓ 测试数据加载完成，共{len(test_data)}个样本")
    
    # 初始化评估器
    evaluator = ModelEvaluator(
        model_path=args.model_path,
        lora_path=args.lora_path
    )
    
    # 【优化】统一生成所有SQL（避免重复生成）
    print(f"\n{'='*50}")
    print("批量生成SQL...")
    print(f"{'='*50}\n")
    print(f"批量大小: {args.batch_size}")
    
    all_predictions = []
    all_references = []
    all_questions = []
    
    for i in tqdm(range(0, len(test_data), args.batch_size), desc="生成SQL"):
        batch = test_data[i:i+args.batch_size]
        
        batch_prompts = []
        batch_references = []
        batch_questions = []
        
        for item in batch:
            question = item.get('question', '')
            reference_sql = item.get('sql', '')
            prompt = build_prompt(question, is_training=False)
            
            batch_prompts.append(prompt)
            batch_references.append(reference_sql)
            batch_questions.append(question)
        
        # 批量生成SQL
        batch_predictions = evaluator.generate_sql_batch(batch_prompts)
        
        all_predictions.extend(batch_predictions)
        all_references.extend(batch_references)
        all_questions.extend(batch_questions)
    
    print(f"✓ SQL生成完成，共 {len(all_predictions)} 条")
    
    # 初始化指标变量
    text_metrics = None
    sql_metrics = None
    
    # 评估文本匹配
    if args.eval_text_match:
        print(f"\n{'='*50}")
        print("评估文本匹配...")
        print(f"{'='*50}\n")
        
        # 计算指标
        exact_match_acc = calculate_exact_match(all_predictions, all_references)
        avg_f1 = calculate_average_f1(all_predictions, all_references)
        
        text_metrics = {
            'exact_match': exact_match_acc,
            'token_f1': avg_f1,
            'total_samples': len(test_data)
        }
        
        print(f"文本匹配评估结果:")
        print(f"  样本总数: {text_metrics['total_samples']}")
        print(f"  精确匹配准确率: {text_metrics['exact_match']:.2%}")
        print(f"  Token级F1分数: {text_metrics['token_f1']:.4f}")
        
        # 保存详细结果
        text_match_output = os.path.join(args.output_dir, "text_match_results.json")
        results = []
        for q, ref, pred in zip(all_questions, all_references, all_predictions):
            results.append({
                'question': q.strip(),
                'reference': ref.strip(),
                'prediction': pred.strip(),
                'exact_match': normalize_sql(pred) == normalize_sql(ref)
            })
        
        output_data = {
            'metrics': text_metrics,
            'results': results
        }
        with open(text_match_output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ 详细结果已保存到: {text_match_output}")
    
    # 评估SQL执行
    if args.eval_sql_execution:
        if not args.db_host:
            print("\n[警告] 未提供数据库连接信息，跳过SQL执行评估")
        else:
            print(f"\n{'='*50}")
            print("评估SQL执行...")
            print(f"{'='*50}\n")
            
            # 初始化数据库执行器并建立连接
            db_executor = SQLExecutor(
                host=args.db_host,
                port=args.db_port,
                user=args.db_user,
                password=args.db_password,
                database=args.db_name
            )
            
            # 使用 with 语句自动管理连接
            with db_executor:
                print("✓ 数据库连接成功")
                
                # 执行SQL验证（使用已生成的SQL）
                total_samples = 0
                execution_success = 0
                result_match = 0
                reference_exec_success = 0
                results = []
                
                for question, reference_sql, predicted_sql in tqdm(
                    zip(all_questions, all_references, all_predictions),
                    total=len(all_predictions),
                    desc="执行SQL"
                ):
                    # 执行参考SQL
                    ref_success, reference_result = db_executor.execute_sql(reference_sql)
                    if ref_success:
                        reference_exec_success += 1
                    
                    # 执行预测SQL
                    pred_success, predicted_result = db_executor.execute_sql(predicted_sql)
                    if pred_success:
                        execution_success += 1
                    
                    # 比较结果
                    is_match = False
                    if ref_success and pred_success:
                        is_match = (reference_result == predicted_result)
                        if is_match:
                            result_match += 1
                    
                    total_samples += 1
                    
                    # 记录详细结果
                    result_detail = {
                        'question': question.strip(),
                        'reference_sql': reference_sql.strip(),
                        'predicted_sql': predicted_sql.strip(),
                        'reference_executed': ref_success,
                        'prediction_executed': pred_success,
                        'results_match': is_match,
                    }
                    
                    if ref_success:
                        result_detail['reference_result_count'] = len(reference_result) if isinstance(reference_result, (list, tuple)) else 0
                    else:
                        result_detail['reference_error'] = str(reference_result)
                    
                    if pred_success:
                        result_detail['predicted_result_count'] = len(predicted_result) if isinstance(predicted_result, (list, tuple)) else 0
                    else:
                        result_detail['prediction_error'] = str(predicted_result)
                    
                    results.append(result_detail)
                
                # 计算指标
                sql_metrics = {
                    'total_samples': total_samples,
                    'reference_execution_rate': reference_exec_success / total_samples if total_samples > 0 else 0,
                    'prediction_execution_rate': execution_success / total_samples if total_samples > 0 else 0,
                    'execution_match_rate': result_match / total_samples if total_samples > 0 else 0,
                    'execution_match_rate_of_valid': result_match / reference_exec_success if reference_exec_success > 0 else 0
                }
                
                print(f"\nSQL执行评估结果:")
                print(f"  样本总数: {sql_metrics['total_samples']}")
                print(f"  参考SQL执行成功率: {sql_metrics['reference_execution_rate']:.2%}")
                print(f"  预测SQL执行成功率: {sql_metrics['prediction_execution_rate']:.2%}")
                print(f"  结果匹配率（全部样本）: {sql_metrics['execution_match_rate']:.2%}")
                print(f"  结果匹配率（有效样本）: {sql_metrics['execution_match_rate_of_valid']:.2%}")
                
                # 如果执行失败，显示前几个错误
                if reference_exec_success == 0:
                    print(f"\n⚠️  警告：所有参考SQL都执行失败！显示前3个错误：")
                    for i, result in enumerate(results[:3]):
                        if not result['reference_executed']:
                            print(f"\n样本 {i+1}:")
                            print(f"  SQL: {result['reference_sql'][:80]}...")
                            print(f"  错误: {result.get('reference_error', 'Unknown error')}")
                
                if execution_success == 0:
                    print(f"\n⚠️  警告：所有预测SQL都执行失败！显示前3个错误：")
                    for i, result in enumerate(results[:3]):
                        if not result['prediction_executed']:
                            print(f"\n样本 {i+1}:")
                            print(f"  SQL: {result['predicted_sql'][:80]}...")
                            print(f"  错误: {result.get('prediction_error', 'Unknown error')}")
                
                # 保存详细结果
                sql_exec_output = os.path.join(args.output_dir, "sql_execution_results.json")
                output_data = {
                    'metrics': sql_metrics,
                    'results': results
                }
                with open(sql_exec_output, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
                print(f"\n✓ 详细结果已保存到: {sql_exec_output}")
    
    # 保存总结
    summary_path = os.path.join(args.output_dir, "evaluation_summary.json")
    summary = {
        'model_path': args.model_path,
        'lora_path': args.lora_path,
        'test_data': args.test_data,
        'num_samples': len(test_data)
    }
    
    if args.eval_text_match and text_metrics:
        summary['text_match_metrics'] = text_metrics
    
    if args.eval_sql_execution and args.db_host and sql_metrics:
        summary['sql_execution_metrics'] = sql_metrics
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*50}")
    print("评估完成！")
    print(f"{'='*50}")
    print(f"✓ 评估总结已保存到: {summary_path}")


if __name__ == "__main__":
    main()
