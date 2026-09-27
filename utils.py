"""
工具函数模块
包含数据加载、SQL执行、评估指标等功能
"""

import json
import pymysql
import sqlparse
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
import re


# ============= 数据加载器 =============

def load_data(file_path: str, data_format: str = "auto") -> List[Dict[str, Any]]:
    """
    加载训练/验证数据
    
    Args:
        file_path: 数据文件路径
        data_format: 数据格式，支持 "alpaca", "sharegpt", "auto"（自动检测）
    
    Returns:
        标准化的数据列表，每条数据包含 question 和 sql 字段
    """
    # 判断文件格式：JSONL（每行一个JSON）还是JSON（整个文件是JSON数组）
    if file_path.endswith('.jsonl'):
        # JSONL 格式：每行一个 JSON 对象
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:  # 跳过空行
                    data.append(json.loads(line))
    else:
        # 标准 JSON 格式：整个文件是一个 JSON 数组
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    if not data:
        raise ValueError(f"数据文件 {file_path} 为空")
    
    # 自动检测数据格式
    if data_format == "auto":
        first_item = data[0]
        if "conversations" in first_item:
            data_format = "sharegpt"
        elif "instruction" in first_item:
            data_format = "alpaca"
        else:
            raise ValueError(f"无法识别的数据格式，请指定 data_format 参数")
    
    # 解析不同格式的数据
    if data_format == "alpaca":
        return parse_alpaca_data(data)
    elif data_format == "sharegpt":
        return parse_sharegpt_data(data)
    else:
        raise ValueError(f"不支持的数据格式: {data_format}")


def parse_alpaca_data(data: List[Dict]) -> List[Dict[str, Any]]:
    """
    解析 Alpaca 格式数据
    格式：{"instruction": "...", "input": "...", "output": "..."}
    """
    parsed_data = []
    for item in data:
        instruction = item.get("instruction", "")
        input_text = item.get("input", "")
        output = item.get("output", "")
        
        # 组合 instruction 和 input 作为问题
        if input_text:
            question = f"{instruction}\n{input_text}".strip()
        else:
            question = instruction.strip()
        
        parsed_data.append({
            "question": question,
            "sql": output.strip()
        })
    
    return parsed_data


def parse_sharegpt_data(data: List[Dict]) -> List[Dict[str, Any]]:
    """
    解析 ShareGPT 格式数据
    格式：{"conversations": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
    """
    parsed_data = []
    for item in data:
        conversations = item.get("conversations", [])
        if len(conversations) < 2:
            continue
        
        # 提取用户问题和助手回答
        question = None
        sql = None
        
        for conv in conversations:
            role = conv.get("role", "")
            content = conv.get("content", "")
            
            if role in ["user", "human"]:
                question = content.strip()
            elif role in ["assistant", "gpt"]:
                sql = content.strip()
        
        if question and sql:
            parsed_data.append({
                "question": question,
                "sql": sql
            })
    
    return parsed_data


# ============= Prompt 模板 =============

def build_prompt(question: str, is_training: bool = True, sql: str = None) -> str:
    """
    构建适配 DeepSeek Coder 的 Prompt
    
    Args:
        question: 自然语言问题
        is_training: 是否为训练模式（包含答案）
        sql: SQL答案（仅在训练模式需要）
    
    Returns:
        格式化的 prompt
    """
    system_prompt = """你是一个专业的SQL专家，能够将自然语言问题转换为准确的SQL查询语句。
请根据用户的问题，生成对应的SQL查询语句。只输出SQL语句，不要包含任何解释。"""
    
    if is_training:
        # 训练模式：包含问题和答案
        prompt = f"""{system_prompt}

### 问题:
{question}

### SQL:
{sql}"""
    else:
        # 推理模式：只包含问题
        prompt = f"""{system_prompt}

### 问题:
{question}

### SQL:
"""
    
    return prompt


def build_chat_prompt(question: str) -> List[Dict[str, str]]:
    """
    构建 Chat 格式的 Prompt（用于推理）
    
    Args:
        question: 自然语言问题
    
    Returns:
        Chat 格式的消息列表
    """
    return [
        {
            "role": "system",
            "content": "你是一个专业的SQL专家，能够将自然语言问题转换为准确的SQL查询语句。请根据用户的问题，生成对应的SQL查询语句。只输出SQL语句，不要包含任何解释。"
        },
        {
            "role": "user",
            "content": question
        }
    ]


# ============= SQL 执行器 =============

class SQLExecutor:
    """MySQL SQL 执行器（支持连接复用）"""
    
    def __init__(self, host: str, port: int, user: str, password: str, database: str, timeout: int = 5):
        """
        初始化数据库连接配置
        
        Args:
            host: 数据库主机地址
            port: 数据库端口
            user: 数据库用户名
            password: 数据库密码
            database: 数据库名称
            timeout: 执行超时时间（秒）
        """
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8mb4',
            'connect_timeout': timeout
        }
        self.timeout = timeout
        self.connection = None
    
    def connect(self):
        """建立数据库连接"""
        if self.connection is None or not self._is_connected():
            try:
                self.connection = pymysql.connect(**self.config)
            except Exception as e:
                raise Exception(f"数据库连接失败: {str(e)}")
    
    def _is_connected(self) -> bool:
        """检查连接是否有效"""
        if self.connection is None:
            return False
        try:
            self.connection.ping(reconnect=False)
            return True
        except:
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None
    
    def execute_sql(self, sql: str) -> Tuple[bool, Any]:
        """
        执行 SQL 查询（复用连接）
        
        Args:
            sql: SQL 查询语句
        
        Returns:
            (是否成功, 结果或错误信息)
        """
        # 安全检查：只允许 SELECT 查询
        sql_clean = sql.strip().upper()
        if not sql_clean.startswith('SELECT'):
            return False, "只允许执行 SELECT 查询"
        
        try:
            # 确保连接可用
            self.connect()
            
            with self.connection.cursor() as cursor:
                # 设置查询超时
                cursor.execute(f"SET SESSION max_execution_time={self.timeout * 1000}")
                
                # 执行查询
                cursor.execute(sql)
                result = cursor.fetchall()
                
                return True, result
        
        except pymysql.Error as e:
            return False, f"数据库错误: {str(e)}"
        except Exception as e:
            return False, f"执行错误: {str(e)}"
    
    def execute_batch(self, sqls: List[str]) -> List[Tuple[bool, Any]]:
        """
        批量执行SQL（复用单个连接，显著提速）
        
        Args:
            sqls: SQL查询列表
        
        Returns:
            结果列表 [(是否成功, 结果或错误信息), ...]
        """
        results = []
        self.connect()  # 建立一次连接
        
        for sql in sqls:
            result = self.execute_sql(sql)
            results.append(result)
        
        return results
    
    def __enter__(self):
        """支持 with 语句"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持 with 语句"""
        self.close()
        return False
    
    def compare_results(self, sql1: str, sql2: str) -> Tuple[bool, str]:
        """
        比较两个 SQL 查询的执行结果是否一致
        
        Args:
            sql1: SQL 查询1（通常是生成的SQL）
            sql2: SQL 查询2（通常是标准SQL）
        
        Returns:
            (是否一致, 说明信息)
        """
        # 执行第一个 SQL
        success1, result1 = self.execute_sql(sql1)
        if not success1:
            return False, f"SQL1 执行失败: {result1}"
        
        # 执行第二个 SQL
        success2, result2 = self.execute_sql(sql2)
        if not success2:
            return False, f"SQL2 执行失败: {result2}"
        
        # 比较结果
        if result1 == result2:
            return True, "结果一致"
        else:
            return False, f"结果不一致。SQL1返回{len(result1)}行，SQL2返回{len(result2)}行"


# ============= 评估指标 =============

def normalize_sql(sql: str) -> str:
    """
    标准化 SQL 语句（用于比较）
    - 移除多余空格
    - 转换为小写
    - 格式化
    """
    # 使用 sqlparse 格式化
    formatted = sqlparse.format(sql, keyword_case='lower', strip_comments=True, reindent=False)
    
    # 移除多余空格和换行
    normalized = ' '.join(formatted.split())
    
    return normalized.strip()


def calculate_exact_match(predictions: List[str], references: List[str]) -> float:
    """
    计算精确匹配准确率
    
    Args:
        predictions: 预测的 SQL 列表
        references: 参考的 SQL 列表
    
    Returns:
        精确匹配准确率
    """
    if len(predictions) != len(references):
        raise ValueError("预测和参考数据长度不一致")
    
    correct = 0
    for pred, ref in zip(predictions, references):
        pred_normalized = normalize_sql(pred)
        ref_normalized = normalize_sql(ref)
        
        if pred_normalized == ref_normalized:
            correct += 1
    
    return correct / len(predictions) if predictions else 0.0


def calculate_token_f1(prediction: str, reference: str) -> float:
    """
    计算 Token 级别的 F1 分数
    
    Args:
        prediction: 预测的 SQL
        reference: 参考的 SQL
    
    Returns:
        F1 分数
    """
    # 分词（简单按空格和特殊字符分割）
    pred_tokens = set(re.findall(r'\w+', prediction.lower()))
    ref_tokens = set(re.findall(r'\w+', reference.lower()))
    
    if not pred_tokens or not ref_tokens:
        return 0.0
    
    # 计算交集
    common = pred_tokens & ref_tokens
    
    if not common:
        return 0.0
    
    # 计算 Precision 和 Recall
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(ref_tokens)
    
    # 计算 F1
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return f1


def calculate_average_f1(predictions: List[str], references: List[str]) -> float:
    """
    计算平均 F1 分数
    
    Args:
        predictions: 预测的 SQL 列表
        references: 参考的 SQL 列表
    
    Returns:
        平均 F1 分数
    """
    if len(predictions) != len(references):
        raise ValueError("预测和参考数据长度不一致")
    
    total_f1 = 0.0
    for pred, ref in zip(predictions, references):
        total_f1 += calculate_token_f1(pred, ref)
    
    return total_f1 / len(predictions) if predictions else 0.0


def calculate_execution_accuracy(
    predictions: List[str], 
    references: List[str], 
    executor: SQLExecutor
) -> Dict[str, float]:
    """
    计算基于执行结果的准确率
    
    Args:
        predictions: 预测的 SQL 列表
        references: 参考的 SQL 列表
        executor: SQL 执行器
    
    Returns:
        包含各项指标的字典
    """
    if len(predictions) != len(references):
        raise ValueError("预测和参考数据长度不一致")
    
    total = len(predictions)
    execution_success = 0  # 生成的SQL能成功执行
    result_match = 0  # 执行结果与标准答案一致
    
    for pred, ref in zip(predictions, references):
        # 尝试执行生成的 SQL
        success, result = executor.execute_sql(pred)
        
        if success:
            execution_success += 1
            
            # 比较执行结果
            match, _ = executor.compare_results(pred, ref)
            if match:
                result_match += 1
    
    return {
        "execution_success_rate": execution_success / total if total > 0 else 0.0,
        "result_match_rate": result_match / total if total > 0 else 0.0
    }


# ============= 其他工具函数 =============

def extract_sql_from_output(output: str) -> str:
    """
    从模型输出中提取 SQL 语句
    模型可能输出额外的解释文本，需要提取纯 SQL
    
    Args:
        output: 模型的原始输出
    
    Returns:
        提取的 SQL 语句
    """
    # 如果输出包含代码块标记，提取其中的内容
    if "```sql" in output.lower():
        match = re.search(r'```sql\s*(.*?)\s*```', output, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    
    if "```" in output:
        match = re.search(r'```\s*(.*?)\s*```', output, re.DOTALL)
        if match:
            return match.group(1).strip()
    
    # 尝试提取 SELECT 语句
    lines = output.split('\n')
    sql_lines = []
    in_sql = False
    
    for line in lines:
        line_upper = line.strip().upper()
        if line_upper.startswith('SELECT'):
            in_sql = True
        
        if in_sql:
            sql_lines.append(line.strip())
            # SQL 语句通常以分号结尾
            if line.strip().endswith(';'):
                break
    
    if sql_lines:
        return ' '.join(sql_lines)
    
    # 如果都没找到，返回原始输出
    return output.strip()


if __name__ == "__main__":
    # 测试代码
    print("工具函数模块加载成功！")
    
    # 测试数据加载
    test_alpaca = [
        {"instruction": "查询所有用户", "input": "", "output": "SELECT * FROM users;"}
    ]
    test_sharegpt = [
        {
            "conversations": [
                {"role": "user", "content": "查询所有用户"},
                {"role": "assistant", "content": "SELECT * FROM users;"}
            ]
        }
    ]
    
    print("\n测试 Alpaca 格式解析:")
    print(parse_alpaca_data(test_alpaca))
    
    print("\n测试 ShareGPT 格式解析:")
    print(parse_sharegpt_data(test_sharegpt))
    
    print("\n测试 Prompt 构建:")
    print(build_prompt("查询所有用户", is_training=True, sql="SELECT * FROM users;"))
