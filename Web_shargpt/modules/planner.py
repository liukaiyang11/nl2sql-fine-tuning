"""
主题规划器模块（LLM阶段A）
基于表卡片，调用LLM生成主题划分和表集合规划
"""

import json
import logging
from typing import Dict, List, Any
from .llm_client import LLMClient
from .table_cards import TableCardsGenerator

logger = logging.getLogger(__name__)


class TopicPlanner:
    """主题规划器类"""
    
    def __init__(self, llm_client: LLMClient, table_cards: Dict[str, Dict[str, Any]]):
        """
        初始化主题规划器
        
        Args:
            llm_client: LLM客户端实例
            table_cards: 表卡片字典
        """
        self.llm_client = llm_client
        self.table_cards = table_cards
        
    def generate_plan(
        self,
        total_samples: int,
        min_tables: int = 3,
        max_tables: int = 8,
        dialect: str = "mysql"
    ) -> Dict[str, Any]:
        """
        生成主题规划
        
        Args:
            total_samples: 总样本数量
            min_tables: 每个主题最小表数量
            max_tables: 每个主题最大表数量
            dialect: SQL方言
            
        Returns:
            规划字典，包含topics列表
        """
        logger.info(f"开始生成主题规划，目标样本数: {total_samples}")
        
        # 将表卡片转换为文本
        generator = TableCardsGenerator(self.table_cards)
        table_cards_text = generator.get_table_cards_text(self.table_cards)
        
        # 构建提示词
        prompt = self._build_planning_prompt(
            table_cards_text,
            total_samples,
            min_tables,
            max_tables,
            dialect
        )
        
        # 调用LLM生成规划
        try:
            plan_data = self.llm_client.call_llm(prompt, expect_json=True)
            
            # 验证和调整规划
            plan = self._validate_and_adjust_plan(plan_data, total_samples, min_tables, max_tables)
            
            logger.info(f"成功生成规划，包含 {len(plan['topics'])} 个主题")
            return plan
            
        except Exception as e:
            logger.error(f"生成规划失败: {str(e)}")
            raise
    
    def _build_planning_prompt(
        self,
        table_cards_text: str,
        total_samples: int,
        min_tables: int,
        max_tables: int,
        dialect: str
    ) -> str:
        """
        构建规划提示词
        
        Args:
            table_cards_text: 表卡片文本
            total_samples: 总样本数
            min_tables: 最小表数
            max_tables: 最大表数
            dialect: SQL方言
            
        Returns:
            提示词文本
        """
        prompt = f"""你是数据库分析专家。以下是数据库表卡片摘要：

{table_cards_text}

请基于以上数据库结构，规划出若干个业务主题（topics），每个主题选择{min_tables}~{max_tables}张相关联的表，用于生成NL2SQL训练样本。

要求：
1. 主题应该覆盖不同的业务场景（如：用户分析、订单统计、销售报表等）
2. 每个主题的表应该有业务关联性（通过外键或业务逻辑相关）
3. 所有主题的生成样本数总和必须等于 {total_samples}
4. 每个主题至少分配 20 个样本

请输出一个JSON格式的规划，格式如下：
{{
  "topics": [
    {{
      "name": "主题名称",
      "tables": ["table1", "table2", "table3"],
      "reason": "选择这些表的理由",
      "count": 100,
      "dialect": "{dialect}"
    }}
  ]
}}

注意：
- 仅输出JSON，不要包含任何解释文字
- 确保所有count之和等于{total_samples}
- 确保所有表名都在上述表卡片中存在
"""
        return prompt
    
    def _validate_and_adjust_plan(
        self,
        plan_data: Any,
        total_samples: int,
        min_tables: int,
        max_tables: int
    ) -> Dict[str, Any]:
        """
        验证并调整规划
        
        Args:
            plan_data: LLM返回的规划数据
            total_samples: 总样本数
            min_tables: 最小表数
            max_tables: 最大表数
            
        Returns:
            调整后的规划字典
        """
        # 确保plan_data是字典且包含topics
        if isinstance(plan_data, list):
            plan_data = {"topics": plan_data}
        
        if not isinstance(plan_data, dict) or 'topics' not in plan_data:
            raise ValueError("LLM返回的规划格式不正确")
        
        topics = plan_data['topics']
        
        # 验证每个主题
        valid_topics = []
        table_names = set(self.table_cards.keys())
        
        for topic in topics:
            # 检查必需字段
            if not all(key in topic for key in ['name', 'tables', 'count']):
                logger.warning(f"主题缺少必需字段，跳过: {topic}")
                continue
            
            # 验证表名
            topic_tables = [t for t in topic['tables'] if t in table_names]
            if len(topic_tables) < min_tables:
                logger.warning(f"主题 {topic['name']} 的有效表数量不足，跳过")
                continue
            
            if len(topic_tables) > max_tables:
                topic_tables = topic_tables[:max_tables]
            
            topic['tables'] = topic_tables
            valid_topics.append(topic)
        
        if not valid_topics:
            raise ValueError("没有有效的主题规划")
        
        # 调整样本数量，确保总和等于total_samples
        current_total = sum(t['count'] for t in valid_topics)
        
        if current_total != total_samples:
            logger.warning(f"调整样本数量分配: {current_total} -> {total_samples}")
            
            # 如果总样本数太少，减少主题数量
            min_samples_per_topic = 1  # 最少1个样本
            max_topics = max(1, total_samples // min_samples_per_topic)
            
            if len(valid_topics) > max_topics:
                logger.warning(f"样本数太少，减少主题数量: {len(valid_topics)} -> {max_topics}")
                valid_topics = valid_topics[:max_topics]
            
            # 按比例调整
            ratio = total_samples / current_total if current_total > 0 else 1
            remaining = total_samples
            
            for i, topic in enumerate(valid_topics):
                if i < len(valid_topics) - 1:
                    # 确保每个主题至少1个样本，并向上取整
                    allocated = max(1, int(round(topic['count'] * ratio)))
                    topic['count'] = min(allocated, remaining - (len(valid_topics) - i - 1))
                    remaining -= topic['count']
                else:
                    # 最后一个主题分配剩余的样本
                    topic['count'] = max(1, remaining)
        
        return {"topics": valid_topics}
    
    def save_plan(self, plan: Dict[str, Any], output_path: str):
        """
        保存规划到JSON文件
        
        Args:
            plan: 规划字典
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        logger.info(f"规划已保存到: {output_path}")


def generate_and_save_plan(
    llm_client: LLMClient,
    table_cards: Dict[str, Dict[str, Any]],
    total_samples: int,
    output_path: str,
    min_tables: int = 3,
    max_tables: int = 8,
    dialect: str = "mysql"
) -> Dict[str, Any]:
    """
    生成并保存规划的便捷函数
    
    Args:
        llm_client: LLM客户端
        table_cards: 表卡片字典
        total_samples: 总样本数
        output_path: 输出文件路径
        min_tables: 最小表数
        max_tables: 最大表数
        dialect: SQL方言
        
    Returns:
        规划字典
    """
    planner = TopicPlanner(llm_client, table_cards)
    plan = planner.generate_plan(total_samples, min_tables, max_tables, dialect)
    planner.save_plan(plan, output_path)
    return plan

