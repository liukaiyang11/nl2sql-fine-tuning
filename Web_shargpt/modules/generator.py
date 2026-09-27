"""
样本生成器模块（LLM阶段B）
基于主题规划和表DDL，调用LLM生成NL2SQL样本
"""

import json
import logging
from typing import Dict, List, Any
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class SampleGenerator:
    """样本生成器类"""
    
    def __init__(self, llm_client: LLMClient, metadata: Dict[str, Any]):
        """
        初始化样本生成器
        
        Args:
            llm_client: LLM客户端实例
            metadata: 元数据字典
        """
        self.llm_client = llm_client
        self.metadata = metadata
        
    def generate_samples(self, plan: Dict[str, Any], dialect: str = "mysql") -> List[Dict[str, str]]:
        """
        根据规划生成样本
        
        Args:
            plan: 主题规划字典
            dialect: SQL方言
            
        Returns:
            样本列表，每个样本格式: {"input": "问题", "output": "SQL"}
        """
        logger.info("开始生成NL2SQL样本...")
        
        all_samples = []
        topics = plan.get('topics', [])
        
        for i, topic in enumerate(topics, 1):
            logger.info(f"处理主题 {i}/{len(topics)}: {topic['name']} (目标: {topic['count']}条)")
            
            try:
                # 生成该主题的样本
                topic_samples = self._generate_topic_samples(topic, dialect)
                all_samples.extend(topic_samples)
                logger.info(f"主题 {topic['name']} 生成了 {len(topic_samples)} 条样本")
                
            except Exception as e:
                logger.error(f"主题 {topic['name']} 生成失败: {str(e)}")
                continue
        
        logger.info(f"总共生成 {len(all_samples)} 条样本")
        return all_samples
    
    def _generate_topic_samples(self, topic: Dict[str, Any], dialect: str) -> List[Dict[str, str]]:
        """
        为单个主题生成样本
        
        Args:
            topic: 主题信息
            dialect: SQL方言
            
        Returns:
            样本列表
        """
        # 确保count是整数（修复浮点数切片问题）
        target_count = int(round(topic['count']))
        
        # 如果目标数量为0，跳过此主题
        if target_count == 0:
            logger.warning(f"主题 {topic['name']} 的目标样本数为0，跳过")
            return []
        
        # 获取该主题涉及的表的DDL
        ddl_snippet = self._get_simplified_ddl(topic['tables'], dialect)
        
        # 构建生成提示词
        prompt = self._build_generation_prompt(
            topic['name'],
            ddl_snippet,
            target_count,
            dialect
        )
        
        # 调用LLM生成样本
        response = self.llm_client.call_llm(prompt, expect_json=False)
        
        # 解析样本
        samples = self._parse_samples(response)
        
        # 如果生成的样本数量不足，尝试补充
        if len(samples) < target_count:
            logger.warning(f"生成样本不足: {len(samples)}/{target_count}，尝试补充...")
            remaining = target_count - len(samples)
            
            try:
                additional_samples = self._generate_additional_samples(
                    topic['name'],
                    ddl_snippet,
                    remaining,
                    dialect
                )
                samples.extend(additional_samples)
            except Exception as e:
                logger.warning(f"补充样本失败: {str(e)}")
        
        return samples[:target_count]  # 确保不超过目标数量
    
    def _get_simplified_ddl(self, table_names: List[str], dialect: str) -> str:
        """
        获取简化的DDL语句
        
        Args:
            table_names: 表名列表
            dialect: SQL方言
            
        Returns:
            DDL文本
        """
        ddl_lines = []
        
        for table_name in table_names:
            if table_name not in self.metadata:
                logger.warning(f"表 {table_name} 不在元数据中，跳过")
                continue
            
            table_info = self.metadata[table_name]
            
            # 构建CREATE TABLE语句
            ddl_lines.append(f"\nCREATE TABLE {table_name} (")
            
            columns = []
            for col in table_info['columns']:
                col_def = f"  {col['name']} {col['column_type']}"
                
                if not col['nullable']:
                    col_def += " NOT NULL"
                
                if col.get('comment'):
                    col_def += f" COMMENT '{col['comment']}'"
                
                columns.append(col_def)
            
            # 添加主键
            if table_info.get('primary_keys'):
                pk_cols = ", ".join(table_info['primary_keys'])
                columns.append(f"  PRIMARY KEY ({pk_cols})")
            
            ddl_lines.append(",\n".join(columns))
            ddl_lines.append(");")
            
            # 添加外键关系说明（作为注释）
            if table_info.get('foreign_keys'):
                ddl_lines.append(f"-- 外键关系:")
                for col, ref in table_info['foreign_keys'].items():
                    ddl_lines.append(f"--   {col} -> {ref}")
        
        return "\n".join(ddl_lines)
    
    def _build_generation_prompt(
        self,
        topic_name: str,
        ddl_snippet: str,
        count: int,
        dialect: str
    ) -> str:
        """
        构建生成提示词
        
        Args:
            topic_name: 主题名称
            ddl_snippet: DDL片段
            count: 生成数量
            dialect: SQL方言
            
        Returns:
            提示词文本
        """
        prompt = f"""你是SQL开发专家。请基于以下数据库表结构，生成 {count} 条关于"{topic_name}"主题的自然语言问题及对应的SQL查询。

SQL方言: {dialect}

数据库表结构:
{ddl_snippet}

要求:
1. 生成的SQL必须可执行，不要虚构表名或字段名
2. 仅使用上述表结构中的表和字段
3. 问题应该多样化，包括：简单查询、聚合统计、JOIN关联、WHERE条件、GROUP BY分组、ORDER BY排序等
4. 每条样本输出一行JSON格式: {{"input":"自然语言问题","output":"SQL语句"}}
5. 不要添加任何解释文字，只输出JSON行

示例格式:
{{"input":"查询所有用户的姓名和邮箱","output":"SELECT name, email FROM users;"}}
{{"input":"统计每个城市的用户数量","output":"SELECT city, COUNT(*) as user_count FROM users GROUP BY city;"}}

请开始生成 {count} 条样本:
"""
        return prompt
    
    def _parse_samples(self, response: str) -> List[Dict[str, str]]:
        """
        解析LLM响应中的样本
        
        Args:
            response: LLM响应文本
            
        Returns:
            样本列表
        """
        samples = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 跳过注释和非JSON行
            if line.startswith('#') or line.startswith('//'):
                continue
            
            try:
                # 尝试解析JSON
                sample = json.loads(line)
                
                # 验证必需字段
                if 'input' in sample and 'output' in sample:
                    samples.append({
                        "input": sample['input'].strip(),
                        "output": sample['output'].strip()
                    })
                else:
                    logger.warning(f"样本缺少必需字段，跳过: {line[:50]}")
                    
            except json.JSONDecodeError:
                logger.warning(f"无法解析JSON，跳过: {line[:50]}")
                continue
        
        return samples
    
    def _generate_additional_samples(
        self,
        topic_name: str,
        ddl_snippet: str,
        count: int,
        dialect: str
    ) -> List[Dict[str, str]]:
        """
        生成额外的样本（用于补充不足的部分）
        
        Args:
            topic_name: 主题名称
            ddl_snippet: DDL片段
            count: 生成数量
            dialect: SQL方言
            
        Returns:
            样本列表
        """
        prompt = self._build_generation_prompt(topic_name, ddl_snippet, count, dialect)
        response = self.llm_client.call_llm(prompt, expect_json=False)
        return self._parse_samples(response)
    
    def save_samples(self, samples: List[Dict[str, str]], output_path: str):
        """
        保存样本到JSONL文件
        
        Args:
            samples: 样本列表
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        logger.info(f"样本已保存到: {output_path} (共{len(samples)}条)")


def generate_and_save_samples(
    llm_client: LLMClient,
    metadata: Dict[str, Any],
    plan: Dict[str, Any],
    output_path: str,
    dialect: str = "mysql"
) -> List[Dict[str, str]]:
    """
    生成并保存样本的便捷函数
    
    Args:
        llm_client: LLM客户端
        metadata: 元数据字典
        plan: 主题规划
        output_path: 输出文件路径
        dialect: SQL方言
        
    Returns:
        样本列表
    """
    generator = SampleGenerator(llm_client, metadata)
    samples = generator.generate_samples(plan, dialect)
    generator.save_samples(samples, output_path)
    return samples

