"""
元数据提取器模块
从数据库中提取表、列、主外键等元数据信息
"""

import json
import logging
from typing import Dict, List, Any
from .db_connector import DatabaseConnector

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """元数据提取器类"""
    
    def __init__(self, db_connector: DatabaseConnector):
        """
        初始化元数据提取器
        
        Args:
            db_connector: 数据库连接器实例
        """
        self.db_connector = db_connector
        self.db_type = db_connector.db_type
        self.database = db_connector.database
        
    def extract_metadata(self, table_blacklist: List[str] = None) -> Dict[str, Any]:
        """
        提取数据库元数据
        
        Args:
            table_blacklist: 表黑名单列表
            
        Returns:
            元数据字典，格式:
            {
                "table_name": {
                    "columns": [...],
                    "primary_keys": [...],
                    "foreign_keys": {...}
                }
            }
        """
        logger.info(f"开始提取数据库 {self.database} 的元数据...")
        
        if table_blacklist is None:
            table_blacklist = []
        
        metadata = {}
        
        # 提取列信息
        columns_data = self._extract_columns()
        
        # 提取主键信息
        primary_keys = self._extract_primary_keys()
        
        # 提取外键信息
        foreign_keys = self._extract_foreign_keys()
        
        # 组装元数据
        for table_name, columns in columns_data.items():
            # 跳过黑名单中的表
            if table_name in table_blacklist:
                logger.info(f"跳过黑名单表: {table_name}")
                continue
                
            metadata[table_name] = {
                "columns": columns,
                "primary_keys": primary_keys.get(table_name, []),
                "foreign_keys": foreign_keys.get(table_name, {})
            }
        
        logger.info(f"成功提取 {len(metadata)} 个表的元数据")
        return metadata
    
    def _extract_columns(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        提取表列信息
        
        Returns:
            表列信息字典
        """
        if self.db_type == 'mysql':
            query = f"""
            SELECT
                c.TABLE_NAME,
                c.COLUMN_NAME,
                c.DATA_TYPE,
                c.COLUMN_TYPE,
                c.IS_NULLABLE,
                c.COLUMN_KEY,
                c.COLUMN_COMMENT,
                c.ORDINAL_POSITION
            FROM information_schema.COLUMNS c
            WHERE c.TABLE_SCHEMA = '{self.database}'
            ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION
            """
        elif self.db_type == 'postgres':
            query = f"""
            SELECT
                c.table_name as TABLE_NAME,
                c.column_name as COLUMN_NAME,
                c.data_type as DATA_TYPE,
                c.udt_name as COLUMN_TYPE,
                c.is_nullable as IS_NULLABLE,
                '' as COLUMN_KEY,
                '' as COLUMN_COMMENT,
                c.ordinal_position as ORDINAL_POSITION
            FROM information_schema.columns c
            WHERE c.table_schema = 'public'
            ORDER BY c.table_name, c.ordinal_position
            """
        else:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")
        
        results = self.db_connector.execute_query(query)
        
        # 按表组织列信息
        columns_by_table = {}
        for row in results:
            table_name = row['TABLE_NAME']
            if table_name not in columns_by_table:
                columns_by_table[table_name] = []
            
            column_info = {
                "name": row['COLUMN_NAME'],
                "type": row['DATA_TYPE'],
                "column_type": row['COLUMN_TYPE'],
                "nullable": row['IS_NULLABLE'] == 'YES',
                "key": row['COLUMN_KEY'],
                "comment": row.get('COLUMN_COMMENT', ''),
                "position": row['ORDINAL_POSITION']
            }
            columns_by_table[table_name].append(column_info)
        
        logger.info(f"提取了 {len(columns_by_table)} 个表的列信息")
        return columns_by_table
    
    def _extract_primary_keys(self) -> Dict[str, List[str]]:
        """
        提取主键信息
        
        Returns:
            表主键信息字典
        """
        if self.db_type == 'mysql':
            query = f"""
            SELECT
                TABLE_NAME,
                COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = '{self.database}'
              AND CONSTRAINT_NAME = 'PRIMARY'
            ORDER BY TABLE_NAME, ORDINAL_POSITION
            """
        elif self.db_type == 'postgres':
            query = """
            SELECT
                tc.table_name as TABLE_NAME,
                kcu.column_name as COLUMN_NAME
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_schema = 'public'
            ORDER BY tc.table_name, kcu.ordinal_position
            """
        else:
            return {}
        
        results = self.db_connector.execute_query(query)
        
        primary_keys = {}
        for row in results:
            table_name = row['TABLE_NAME']
            if table_name not in primary_keys:
                primary_keys[table_name] = []
            primary_keys[table_name].append(row['COLUMN_NAME'])
        
        logger.info(f"提取了 {len(primary_keys)} 个表的主键信息")
        return primary_keys
    
    def _extract_foreign_keys(self) -> Dict[str, Dict[str, str]]:
        """
        提取外键信息
        
        Returns:
            表外键信息字典，格式: {table: {column: "ref_table.ref_column"}}
        """
        if self.db_type == 'mysql':
            query = f"""
            SELECT
                kcu.TABLE_NAME,
                kcu.COLUMN_NAME,
                kcu.REFERENCED_TABLE_NAME,
                kcu.REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE kcu
            WHERE kcu.TABLE_SCHEMA = '{self.database}'
              AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            """
        elif self.db_type == 'postgres':
            query = """
            SELECT
                kcu.table_name as TABLE_NAME,
                kcu.column_name as COLUMN_NAME,
                ccu.table_name as REFERENCED_TABLE_NAME,
                ccu.column_name as REFERENCED_COLUMN_NAME
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
            """
        else:
            return {}
        
        results = self.db_connector.execute_query(query)
        
        foreign_keys = {}
        for row in results:
            table_name = row['TABLE_NAME']
            if table_name not in foreign_keys:
                foreign_keys[table_name] = {}
            
            column = row['COLUMN_NAME']
            ref_table = row['REFERENCED_TABLE_NAME']
            ref_column = row['REFERENCED_COLUMN_NAME']
            foreign_keys[table_name][column] = f"{ref_table}.{ref_column}"
        
        logger.info(f"提取了 {len(foreign_keys)} 个表的外键信息")
        return foreign_keys
    
    def save_metadata(self, metadata: Dict[str, Any], output_path: str):
        """
        保存元数据到JSON文件
        
        Args:
            metadata: 元数据字典
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        logger.info(f"元数据已保存到: {output_path}")


def extract_and_save_metadata(
    db_connector: DatabaseConnector,
    output_path: str,
    table_blacklist: List[str] = None
) -> Dict[str, Any]:
    """
    提取并保存元数据的便捷函数
    
    Args:
        db_connector: 数据库连接器
        output_path: 输出文件路径
        table_blacklist: 表黑名单
        
    Returns:
        元数据字典
    """
    extractor = MetadataExtractor(db_connector)
    metadata = extractor.extract_metadata(table_blacklist)
    extractor.save_metadata(metadata, output_path)
    return metadata
