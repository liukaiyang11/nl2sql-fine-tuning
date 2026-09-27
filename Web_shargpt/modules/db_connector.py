"""
数据库连接器模块
支持MySQL、PostgreSQL、SQL Server等数据库
"""

import pymysql
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """数据库连接器类"""
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        初始化数据库连接器
        
        Args:
            db_config: 数据库配置字典，包含type、host、port、user、password、database
        """
        self.db_type = db_config.get('type', 'mysql').lower()
        self.host = db_config.get('host', 'localhost')
        self.port = db_config.get('port', 3306)
        self.user = db_config.get('user', 'root')
        self.password = db_config.get('password', '')
        self.database = db_config.get('database', '')
        self.connection = None
        
    def get_connection(self):
        """
        获取数据库连接
        
        Returns:
            数据库连接对象
        """
        try:
            if self.db_type == 'mysql':
                self.connection = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
                logger.info(f"成功连接到MySQL数据库: {self.database}")
                
            elif self.db_type == 'postgres':
                try:
                    import psycopg2
                    from psycopg2.extras import RealDictCursor
                    self.connection = psycopg2.connect(
                        host=self.host,
                        port=self.port,
                        user=self.user,
                        password=self.password,
                        database=self.database
                    )
                    logger.info(f"成功连接到PostgreSQL数据库: {self.database}")
                except ImportError:
                    raise ImportError("PostgreSQL支持需要安装psycopg2: pip install psycopg2-binary")
                    
            elif self.db_type == 'sqlserver':
                try:
                    import pyodbc
                    connection_string = (
                        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                        f"SERVER={self.host},{self.port};"
                        f"DATABASE={self.database};"
                        f"UID={self.user};"
                        f"PWD={self.password}"
                    )
                    self.connection = pyodbc.connect(connection_string)
                    logger.info(f"成功连接到SQL Server数据库: {self.database}")
                except ImportError:
                    raise ImportError("SQL Server支持需要安装pyodbc: pip install pyodbc")
            else:
                raise ValueError(f"不支持的数据库类型: {self.db_type}")
                
            return self.connection
            
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise
    
    def execute_query(self, query: str, params: Optional[tuple] = None):
        """
        执行查询语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        if not self.connection:
            self.get_connection()
            
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                return results
        except Exception as e:
            logger.error(f"查询执行失败: {str(e)}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")
            
    def __enter__(self):
        """上下文管理器入口"""
        self.get_connection()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()


def create_connector(db_config: Dict[str, Any]) -> DatabaseConnector:
    """
    创建数据库连接器的工厂函数
    
    Args:
        db_config: 数据库配置字典
        
    Returns:
        DatabaseConnector实例
    """
    return DatabaseConnector(db_config)
