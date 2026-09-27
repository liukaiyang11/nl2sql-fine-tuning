"""
数据导出器模块
将验证通过的样本导出为LLaMA-Factory可用的训练数据格式
"""

import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class DataExporter:
    """数据导出器类"""
    
    def __init__(self, samples: List[Dict[str, str]]):
        """
        初始化数据导出器
        
        Args:
            samples: 样本列表，格式: [{"input": "...", "output": "..."}]
        """
        self.samples = samples
        
    def export_alpaca(self, output_path: str, instruction: str = None):
        """
        导出为Alpaca格式
        
        Args:
            output_path: 输出文件路径
            instruction: 指令文本（可选）
        """
        if instruction is None:
            instruction = "根据以下数据库表结构，将自然语言问题转换为SQL查询语句。"
        
        logger.info(f"导出Alpaca格式数据到: {output_path}")
        
        # 确保目录存在
        import os
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"创建输出目录: {output_dir}")
        
        alpaca_samples = []
        for sample in self.samples:
            alpaca_sample = {
                "instruction": instruction,
                "input": sample['input'],
                "output": sample['output']
            }
            alpaca_samples.append(alpaca_sample)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in alpaca_samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        
        logger.info(f"成功导出 {len(alpaca_samples)} 条Alpaca格式样本")
    
    def export_sharegpt(self, output_path: str):
        """
        导出为ShareGPT格式
        
        Args:
            output_path: 输出文件路径
        """
        logger.info(f"导出ShareGPT格式数据到: {output_path}")
        
        # 确保目录存在
        import os
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"创建输出目录: {output_dir}")
        
        sharegpt_samples = []
        for sample in self.samples:
            sharegpt_sample = {
                "conversations": [
                    {
                        "role": "user",
                        "content": sample['input']
                    },
                    {
                        "role": "assistant",
                        "content": sample['output']
                    }
                ]
            }
            sharegpt_samples.append(sharegpt_sample)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in sharegpt_samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        
        logger.info(f"成功导出 {len(sharegpt_samples)} 条ShareGPT格式样本")
    
    def export(self, output_path: str, format_type: str = "alpaca", **kwargs):
        """
        导出数据（通用接口）
        
        Args:
            output_path: 输出文件路径
            format_type: 格式类型 (alpaca/sharegpt)
            **kwargs: 其他参数
        """
        if format_type.lower() == "alpaca":
            self.export_alpaca(output_path, kwargs.get('instruction'))
        elif format_type.lower() == "sharegpt":
            self.export_sharegpt(output_path)
        else:
            raise ValueError(f"不支持的导出格式: {format_type}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据统计信息
        
        Returns:
            统计信息字典
        """
        total_samples = len(self.samples)
        
        # 统计SQL类型
        sql_types = {
            'SELECT': 0,
            'INSERT': 0,
            'UPDATE': 0,
            'DELETE': 0,
            'OTHER': 0
        }
        
        # 统计SQL特征
        features = {
            'with_join': 0,
            'with_group_by': 0,
            'with_order_by': 0,
            'with_limit': 0,
            'with_subquery': 0,
            'with_aggregate': 0
        }
        
        for sample in self.samples:
            sql = sample['output'].upper()
            
            # 统计SQL类型
            if sql.startswith('SELECT'):
                sql_types['SELECT'] += 1
            elif sql.startswith('INSERT'):
                sql_types['INSERT'] += 1
            elif sql.startswith('UPDATE'):
                sql_types['UPDATE'] += 1
            elif sql.startswith('DELETE'):
                sql_types['DELETE'] += 1
            else:
                sql_types['OTHER'] += 1
            
            # 统计SQL特征
            if 'JOIN' in sql:
                features['with_join'] += 1
            if 'GROUP BY' in sql:
                features['with_group_by'] += 1
            if 'ORDER BY' in sql:
                features['with_order_by'] += 1
            if 'LIMIT' in sql:
                features['with_limit'] += 1
            if any(sub in sql for sub in ['(SELECT', '( SELECT']):
                features['with_subquery'] += 1
            if any(agg in sql for agg in ['COUNT(', 'SUM(', 'AVG(', 'MAX(', 'MIN(']):
                features['with_aggregate'] += 1
        
        # 计算平均长度
        avg_input_length = sum(len(s['input']) for s in self.samples) / total_samples if total_samples > 0 else 0
        avg_output_length = sum(len(s['output']) for s in self.samples) / total_samples if total_samples > 0 else 0
        
        statistics = {
            'total_samples': total_samples,
            'sql_types': sql_types,
            'features': features,
            'avg_input_length': round(avg_input_length, 2),
            'avg_output_length': round(avg_output_length, 2)
        }
        
        return statistics
    
    def print_statistics(self):
        """打印数据统计信息"""
        stats = self.get_statistics()
        
        logger.info("=" * 60)
        logger.info("数据统计信息")
        logger.info("=" * 60)
        logger.info(f"总样本数: {stats['total_samples']}")
        logger.info(f"平均问题长度: {stats['avg_input_length']} 字符")
        logger.info(f"平均SQL长度: {stats['avg_output_length']} 字符")
        logger.info("")
        logger.info("SQL类型分布:")
        for sql_type, count in stats['sql_types'].items():
            percentage = count / stats['total_samples'] * 100 if stats['total_samples'] > 0 else 0
            logger.info(f"  {sql_type}: {count} ({percentage:.1f}%)")
        logger.info("")
        logger.info("SQL特征统计:")
        for feature, count in stats['features'].items():
            percentage = count / stats['total_samples'] * 100 if stats['total_samples'] > 0 else 0
            logger.info(f"  {feature}: {count} ({percentage:.1f}%)")
        logger.info("=" * 60)


def export_samples(
    samples: List[Dict[str, str]],
    output_path: str,
    format_type: str = "alpaca",
    **kwargs
):
    """
    导出样本的便捷函数
    
    Args:
        samples: 样本列表
        output_path: 输出文件路径
        format_type: 格式类型
        **kwargs: 其他参数
    """
    exporter = DataExporter(samples)
    exporter.print_statistics()
    exporter.export(output_path, format_type, **kwargs)

