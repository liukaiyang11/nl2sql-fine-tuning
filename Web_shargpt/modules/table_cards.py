"""
表卡片生成器模块
将元数据转换为简化的表卡片摘要，便于LLM理解
"""

import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class TableCardsGenerator:
    """表卡片生成器类"""
    
    def __init__(self, metadata: Dict[str, Any]):
        """
        初始化表卡片生成器
        
        Args:
            metadata: 元数据字典
        """
        self.metadata = metadata
        
    def make_table_cards(self) -> Dict[str, Dict[str, Any]]:
        """
        生成表卡片
        
        Returns:
            表卡片字典，格式:
            {
                "table_name": {
                    "summary": "表描述",
                    "columns": [{"name": "...", "type": "...", "desc": "..."}],
                    "foreign_keys": {"column": "ref_table.ref_column"}
                }
            }
        """
        logger.info("开始生成表卡片...")
        
        table_cards = {}
        
        for table_name, table_info in self.metadata.items():
            # 生成表摘要
            summary = self._generate_table_summary(table_name, table_info)
            
            # 简化列信息
            columns = self._simplify_columns(table_info['columns'], table_info['primary_keys'])
            
            # 获取外键信息
            foreign_keys = table_info.get('foreign_keys', {})
            
            table_cards[table_name] = {
                "summary": summary,
                "columns": columns,
                "foreign_keys": foreign_keys
            }
        
        logger.info(f"成功生成 {len(table_cards)} 个表卡片")
        return table_cards
    
    def _generate_table_summary(self, table_name: str, table_info: Dict[str, Any]) -> str:
        """
        生成表摘要
        
        Args:
            table_name: 表名
            table_info: 表信息
            
        Returns:
            表摘要文本
        """
        # 基于表名和列信息生成简单摘要
        column_count = len(table_info['columns'])
        has_fk = len(table_info.get('foreign_keys', {})) > 0
        
        # 尝试从列注释中提取信息
        comments = [col.get('comment', '') for col in table_info['columns'] if col.get('comment')]
        
        # 生成摘要
        summary_parts = [f"{table_name}表"]
        
        if comments:
            summary_parts.append(f"，包含{column_count}个字段")
        else:
            summary_parts.append(f"，包含{column_count}个字段")
        
        if has_fk:
            summary_parts.append("，有外键关联")
        
        return "".join(summary_parts) + "。"
    
    def _simplify_columns(self, columns: List[Dict[str, Any]], primary_keys: List[str]) -> List[Dict[str, str]]:
        """
        简化列信息
        
        Args:
            columns: 原始列信息列表
            primary_keys: 主键列表
            
        Returns:
            简化后的列信息列表
        """
        simplified = []
        
        for col in columns:
            col_name = col['name']
            col_type = col['column_type'] or col['type']
            
            # 生成列描述
            desc_parts = []
            
            if col_name in primary_keys:
                desc_parts.append("主键")
            
            if col.get('comment'):
                desc_parts.append(col['comment'])
            
            if not col['nullable'] and col_name not in primary_keys:
                desc_parts.append("必填")
            
            desc = "，".join(desc_parts) if desc_parts else col_type
            
            simplified.append({
                "name": col_name,
                "type": col_type.upper(),
                "desc": desc
            })
        
        return simplified
    
    def get_table_cards_text(self, table_cards: Dict[str, Dict[str, Any]]) -> str:
        """
        将表卡片转换为文本格式，用于LLM提示词
        
        Args:
            table_cards: 表卡片字典
            
        Returns:
            表卡片文本
        """
        lines = []
        
        for table_name, card in table_cards.items():
            lines.append(f"\n### 表: {table_name}")
            lines.append(f"说明: {card['summary']}")
            lines.append("字段:")
            
            for col in card['columns']:
                lines.append(f"  - {col['name']} ({col['type']}): {col['desc']}")
            
            if card['foreign_keys']:
                lines.append("外键关系:")
                for col, ref in card['foreign_keys'].items():
                    lines.append(f"  - {col} -> {ref}")
        
        return "\n".join(lines)
    
    def save_table_cards(self, table_cards: Dict[str, Dict[str, Any]], output_path: str):
        """
        保存表卡片到JSON文件
        
        Args:
            table_cards: 表卡片字典
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(table_cards, f, ensure_ascii=False, indent=2)
        logger.info(f"表卡片已保存到: {output_path}")


def generate_and_save_table_cards(
    metadata: Dict[str, Any],
    output_path: str
) -> Dict[str, Dict[str, Any]]:
    """
    生成并保存表卡片的便捷函数
    
    Args:
        metadata: 元数据字典
        output_path: 输出文件路径
        
    Returns:
        表卡片字典
    """
    generator = TableCardsGenerator(metadata)
    table_cards = generator.make_table_cards()
    generator.save_table_cards(table_cards, output_path)
    return table_cards
