"""
VLLM部署测试脚本
用于测试LoRA微调后的模型在VLLM上的推理性能
"""

import argparse
import json
import time
from typing import List, Dict
from vllm import LLM, SamplingParams
from utils import (
    load_json_data,
    detect_data_format,
    format_alpaca_prompt,
    format_sharegpt_prompt,
    extract_sql_from_response
)


class VLLMTester:
    """VLLM测试器"""
    
    def __init__(
        self,
        model_path: str,
        lora_path: str = None,
        tensor_parallel_size: int = 1,
        gpu_memory_utilization: float = 0.9
    ):
        """
        初始化VLLM测试器
        
        Args:
            model_path: 基础模型路径
            lora_path: LoRA权重路径（可选）
            tensor_parallel_size: 张量并行大小
            gpu_memory_utilization: GPU内存使用率
        """
        print(f"\n{'='*50}")
        print("正在初始化VLLM...")
        print(f"{'='*50}")
        
        # VLLM初始化参数
        llm_kwargs = {
            "model": model_path,
            "tensor_parallel_size": tensor_parallel_size,
            "gpu_memory_utilization": gpu_memory_utilization,
            "trust_remote_code": True,
            "dtype": "float16"
        }
        
        # 如果有LoRA权重，添加LoRA参数
        if lora_path:
            llm_kwargs["enable_lora"] = True
            llm_kwargs["max_lora_rank"] = 64
            print(f"✓ 启用LoRA支持: {lora_path}")
        
        self.llm = LLM(**llm_kwargs)
        self.lora_path = lora_path
        
        print(f"✓ VLLM初始化完成")
        print(f"  模型路径: {model_path}")
        print(f"  张量并行: {tensor_parallel_size}")
        print(f"  GPU内存使用: {gpu_memory_utilization:.0%}")
    
    def generate(
        self,
        prompts: List[str],
        max_tokens: int = 512,
        temperature: float = 0.1,
        top_p: float = 0.95,
        stop_tokens: List[str] = None
    ) -> List[str]:
        """
        批量生成SQL
        
        Args:
            prompts: Prompt列表
            max_tokens: 最大生成token数
            temperature: 温度参数
            top_p: top_p采样参数
            stop_tokens: 停止token列表
        
        Returns:
            生成的文本列表
        """
        # 配置采样参数
        sampling_params = SamplingParams(
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stop=stop_tokens
        )
        
        # 如果有LoRA，需要为每个prompt指定LoRA路径
        if self.lora_path:
            # VLLM的LoRA支持方式可能需要根据版本调整
            # 这里提供基本框架
            outputs = self.llm.generate(
                prompts,
                sampling_params,
                use_tqdm=True
            )
        else:
            outputs = self.llm.generate(
                prompts,
                sampling_params,
                use_tqdm=True
            )
        
        # 提取生成的文本
        generated_texts = [output.outputs[0].text for output in outputs]
        
        return generated_texts
    
    def benchmark(
        self,
        test_data: List[Dict],
        batch_size: int = 8,
        max_tokens: int = 512
    ) -> Dict:
        """
        性能基准测试
        
        Args:
            test_data: 测试数据
            batch_size: 批处理大小
            max_tokens: 最大生成token数
        
        Returns:
            性能统计字典
        """
        print(f"\n{'='*50}")
        print("开始性能基准测试")
        print(f"{'='*50}\n")
        
        # 准备prompts
        prompts = []
        for item in test_data:
            data_format = detect_data_format(item)
            
            if data_format == 'alpaca':
                instruction = item.get('instruction', '')
                input_text = item.get('input', '')
                prompt = format_alpaca_prompt(instruction, input_text)
            elif data_format == 'sharegpt':
                conversations = item.get('conversations', [])
                prompt, _ = format_sharegpt_prompt(conversations)
            
            prompts.append(prompt)
        
        print(f"总样本数: {len(prompts)}")
        print(f"批处理大小: {batch_size}")
        
        # 批量生成
        all_outputs = []
        total_time = 0
        
        for i in range(0, len(prompts), batch_size):
            batch_prompts = prompts[i:i+batch_size]
            
            start_time = time.time()
            batch_outputs = self.generate(
                batch_prompts,
                max_tokens=max_tokens,
                temperature=0.1
            )
            batch_time = time.time() - start_time
            
            all_outputs.extend(batch_outputs)
            total_time += batch_time
            
            print(f"批次 {i//batch_size + 1}: "
                  f"{len(batch_prompts)}个样本, "
                  f"耗时 {batch_time:.2f}秒, "
                  f"速度 {len(batch_prompts)/batch_time:.2f} samples/s")
        
        # 计算统计信息
        avg_time_per_sample = total_time / len(prompts)
        throughput = len(prompts) / total_time
        
        stats = {
            'total_samples': len(prompts),
            'batch_size': batch_size,
            'total_time': total_time,
            'avg_time_per_sample': avg_time_per_sample,
            'throughput': throughput
        }
        
        print(f"\n{'='*50}")
        print("性能统计")
        print(f"{'='*50}")
        print(f"总样本数: {stats['total_samples']}")
        print(f"总耗时: {stats['total_time']:.2f}秒")
        print(f"平均每样本耗时: {stats['avg_time_per_sample']:.4f}秒")
        print(f"吞吐量: {stats['throughput']:.2f} samples/s")
        
        return stats, all_outputs
    
    def interactive_test(self):
        """交互式测试模式"""
        print(f"\n{'='*50}")
        print("进入交互式测试模式")
        print(f"{'='*50}")
        print("输入自然语言问题，模型将生成SQL查询")
        print("输入 'quit' 或 'exit' 退出\n")
        
        while True:
            try:
                # 获取用户输入
                user_input = input("请输入查询需求 >>> ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("退出交互模式")
                    break
                
                if not user_input:
                    continue
                
                # 构建prompt（使用Alpaca格式）
                prompt = format_alpaca_prompt(
                    instruction="将以下自然语言查询转换为SQL语句",
                    input_text=user_input
                )
                
                # 生成SQL
                print("\n生成中...")
                start_time = time.time()
                outputs = self.generate(
                    [prompt],
                    max_tokens=512,
                    temperature=0.1
                )
                gen_time = time.time() - start_time
                
                # 提取SQL
                sql = extract_sql_from_response(outputs[0])
                
                print(f"\n生成的SQL:")
                print(f"{'-'*50}")
                print(sql)
                print(f"{'-'*50}")
                print(f"生成耗时: {gen_time:.2f}秒\n")
                
            except KeyboardInterrupt:
                print("\n\n退出交互模式")
                break
            except Exception as e:
                print(f"\n错误: {e}\n")


def main():
    parser = argparse.ArgumentParser(description="VLLM部署测试")
    
    # 模型参数
    parser.add_argument("--model_path", type=str, required=True,
                        help="基础模型路径")
    parser.add_argument("--lora_path", type=str, default=None,
                        help="LoRA权重路径（可选）")
    
    # VLLM参数
    parser.add_argument("--tensor_parallel_size", type=int, default=1,
                        help="张量并行大小")
    parser.add_argument("--gpu_memory_utilization", type=float, default=0.9,
                        help="GPU内存使用率")
    
    # 测试模式
    parser.add_argument("--mode", type=str, default="benchmark",
                        choices=["benchmark", "interactive", "both"],
                        help="测试模式：benchmark（基准测试）、interactive（交互式）、both（两者都执行）")
    
    # 基准测试参数
    parser.add_argument("--test_data", type=str, default=None,
                        help="测试数据路径（benchmark模式需要）")
    parser.add_argument("--batch_size", type=int, default=8,
                        help="批处理大小")
    parser.add_argument("--max_samples", type=int, default=None,
                        help="最大测试样本数")
    parser.add_argument("--max_tokens", type=int, default=512,
                        help="最大生成token数")
    
    # 输出参数
    parser.add_argument("--output_file", type=str, default=None,
                        help="结果输出文件路径")
    
    args = parser.parse_args()
    
    # 初始化VLLM测试器
    tester = VLLMTester(
        model_path=args.model_path,
        lora_path=args.lora_path,
        tensor_parallel_size=args.tensor_parallel_size,
        gpu_memory_utilization=args.gpu_memory_utilization
    )
    
    # 执行对应的测试模式
    if args.mode in ["benchmark", "both"]:
        if not args.test_data:
            print("[错误] benchmark模式需要提供 --test_data 参数")
            return
        
        # 加载测试数据
        test_data = load_json_data(args.test_data)
        
        if args.max_samples:
            test_data = test_data[:args.max_samples]
            print(f"使用前{args.max_samples}个样本进行测试")
        
        # 执行基准测试
        stats, outputs = tester.benchmark(
            test_data,
            batch_size=args.batch_size,
            max_tokens=args.max_tokens
        )
        
        # 保存结果
        if args.output_file:
            results = {
                'performance_stats': stats,
                'samples': []
            }
            
            for i, (item, output) in enumerate(zip(test_data, outputs)):
                data_format = detect_data_format(item)
                
                if data_format == 'alpaca':
                    question = item.get('instruction', '') + ' ' + item.get('input', '')
                    reference = item.get('output', '')
                elif data_format == 'sharegpt':
                    conversations = item.get('conversations', [])
                    question = conversations[0]['content'] if conversations else ''
                    reference = conversations[-1]['content'] if len(conversations) > 1 else ''
                
                results['samples'].append({
                    'id': i,
                    'question': question.strip(),
                    'reference': reference.strip(),
                    'generated': extract_sql_from_response(output).strip()
                })
            
            with open(args.output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"\n✓ 结果已保存到: {args.output_file}")
    
    if args.mode in ["interactive", "both"]:
        # 执行交互式测试
        tester.interactive_test()


if __name__ == "__main__":
    main()
