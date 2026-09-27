"""
SQL校验器模块
使用sqlglot进行语法检查，并验证表名和字段的有效性
"""

import json
import logging
from typing import Dict, List, Any, Optional
import sqlglot
from sqlglot import parse_one, exp
from .db_connector import DatabaseConnector

logger = logging.getLogger(__name__)


class SQLValidator:
    """SQL校验器类"""
    
    def __init__(
        self,
        metadata: Dict[str, Any],
        db_connector: Optional[DatabaseConnector] = None,
        enable_execution_check: bool = False
    ):
        """
        初始化SQL校验器
        
        Args:
            metadata: 元数据字典
            db_connector: 数据库连接器（可选，用于执行验证）
            enable_execution_check: 是否启用执行验证
        """
        self.metadata = metadata
        self.db_connector = db_connector
        self.enable_execution_check = enable_execution_check
        
        # 构建表和字段的快速查找索引
        self._build_schema_index()
        
    def _build_schema_index(self):
        """构建schema索引用于快速查找"""
        self.table_columns = {}
        
        for table_name, table_info in self.metadata.items():
            # 存储表的所有列名（小写，用于不区分大小写的比较）
            columns = {col['name'].lower() for col in table_info['columns']}
            self.table_columns[table_name.lower()] = columns
    
    def validate_samples(
        self,
        samples: List[Dict[str, str]],
        dialect: str = "mysql"
    ) -> List[Dict[str, str]]:
        """
        验证样本列表
        
        Args:
            samples: 样本列表
            dialect: SQL方言
            
        Returns:
            验证通过的样本列表
        """
        logger.info(f"开始验证 {len(samples)} 条样本...")
        
        valid_samples = []
        invalid_count = 0
        
        for i, sample in enumerate(samples, 1):
            sql = sample.get('output', '').strip()
            
            if not sql:
                logger.warning(f"样本 {i} 没有SQL语句，跳过")
                invalid_count += 1
                continue
            
            # 验证SQL
            is_valid, error_msg = self.validate_sql(sql, dialect)
            
            if is_valid:
                valid_samples.append(sample)
            else:
                logger.warning(f"样本 {i} 验证失败: {error_msg[:100]}")
                invalid_count += 1
            
            # 每100条记录一次进度
            if i % 100 == 0:
                logger.info(f"已验证 {i}/{len(samples)} 条样本")
        
        logger.info(f"验证完成: 有效 {len(valid_samples)} 条, 无效 {invalid_count} 条")
        return valid_samples
    
    def validate_sql(self, sql: str, dialect: str = "mysql") -> tuple[bool, str]:
        """
        验证单条SQL语句
        
        Args:
            sql: SQL语句
            dialect: SQL方言
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 1. 语法检查
            is_valid, error = self._check_syntax(sql, dialect)
            if not is_valid:
                return False, f"语法错误: {error}"
            
            # 2. Schema验证（表名和字段名）
            is_valid, error = self._check_schema(sql, dialect)
            if not is_valid:
                return False, f"Schema错误: {error}"
            
            # 3. 可选：执行验证
            if self.enable_execution_check and self.db_connector:
                is_valid, error = self._check_execution(sql)
                if not is_valid:
                    return False, f"执行错误: {error}"
            
            return True, ""
            
        except Exception as e:
            return False, str(e)
    
    def _check_syntax(self, sql: str, dialect: str) -> tuple[bool, str]:
        """
        检查SQL语法
        
        Args:
            sql: SQL语句
            dialect: SQL方言
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 使用sqlglot解析SQL
            parsed = parse_one(sql, read=dialect)
            
            if parsed is None:
                return False, "无法解析SQL语句"
            
            return True, ""
            
        except Exception as e:
            return False, str(e)
    
    def _check_schema(self, sql: str, dialect: str) -> tuple[bool, str]:
        """
        检查SQL中的表名和字段名是否存在
        
        Args:
            sql: SQL语句
            dialect: SQL方言
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            parsed = parse_one(sql, read=dialect)
            
            # 构建别名映射：别名 -> 实际表名
            alias_to_table = {}
            
            # 提取所有表名和别名
            tables = []
            for table in parsed.find_all(exp.Table):
                # 获取实际表名（this属性包含实际表名）
                if hasattr(table, 'this') and table.this:
                    actual_table_name = str(table.this).lower()
                else:
                    actual_table_name = table.name.lower()
                
                tables.append(actual_table_name)
                
                # 检查表是否存在
                if actual_table_name not in self.table_columns:
                    return False, f"表 '{actual_table_name}' 不存在"
                
                # 如果有别名，记录别名映射
                if hasattr(table, 'alias') and table.alias:
                    alias = str(table.alias).lower()
                    alias_to_table[alias] = actual_table_name
                else:
                    # 如果没有别名，表名本身也可以作为引用
                    alias_to_table[actual_table_name] = actual_table_name
            
            # 提取所有列引用
            for column in parsed.find_all(exp.Column):
                column_name = column.name.lower()
                table_ref = None
                
                # 如果列有表限定符（可能是表名或别名）
                if column.table:
                    table_ref = column.table.lower()
                
                    # 将别名或表名映射到实际表名
                    if table_ref in alias_to_table:
                        actual_table = alias_to_table[table_ref]
                    else:
                        # 如果不在映射中，可能是直接使用表名（没有别名）
                        actual_table = table_ref
                    
                    # 验证实际表名是否存在
                    if actual_table not in self.table_columns:
                        return False, f"表 '{actual_table}' 不存在"
                    
                    # 验证列是否存在
                    if column_name != '*' and column_name not in self.table_columns[actual_table]:
                        return False, f"字段 '{actual_table}.{column_name}' 不存在"
                else:
                    # 没有表限定符的列，检查是否在任何相关表中
                    if column_name != '*':  # 跳过SELECT *
                        found = False
                        for tbl in tables:
                            if tbl in self.table_columns and column_name in self.table_columns[tbl]:
                                found = True
                                break
                        
                        # 如果没找到，可能是聚合函数或别名，暂时跳过
                        # （更严格的验证需要完整的语义分析）
            
            return True, ""
            
        except Exception as e:
            return False, str(e)
    
    def _check_execution(self, sql: str) -> tuple[bool, str]:
        """
        执行SQL验证（只读验证，自动添加LIMIT）
        
        Args:
            sql: SQL语句
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 确保是SELECT语句
            if not sql.strip().upper().startswith('SELECT'):
                return True, ""  # 非SELECT语句跳过执行验证
            
            # 添加LIMIT以限制结果集
            test_sql = sql.strip()
            if 'LIMIT' not in test_sql.upper():
                # 移除末尾的分号
                if test_sql.endswith(';'):
                    test_sql = test_sql[:-1]
                test_sql += ' LIMIT 1'
            
            # 执行查询
            self.db_connector.execute_query(test_sql)
            return True, ""
            
        except Exception as e:
            return False, str(e)
    
    def save_valid_samples(self, samples: List[Dict[str, str]], output_path: str):
        """
        保存验证通过的样本
        
        Args:
            samples: 样本列表
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        logger.info(f"有效样本已保存到: {output_path} (共{len(samples)}条)")


def validate_and_save_samples(
    samples: List[Dict[str, str]],
    metadata: Dict[str, Any],
    output_path: str,
    dialect: str = "mysql",
    db_connector: Optional[DatabaseConnector] = None,
    enable_execution_check: bool = False
) -> List[Dict[str, str]]:
    """
    验证并保存样本的便捷函数
    
    Args:
        samples: 样本列表
        metadata: 元数据字典
        output_path: 输出文件路径
        dialect: SQL方言
        db_connector: 数据库连接器
        enable_execution_check: 是否启用执行验证
        
    Returns:
        有效样本列表
    """
    validator = SQLValidator(metadata, db_connector, enable_execution_check)
    valid_samples = validator.validate_samples(samples, dialect)
    validator.save_valid_samples(valid_samples, output_path)
    return valid_samples

