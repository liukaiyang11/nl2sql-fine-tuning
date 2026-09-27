"""
LLM客户端模块
支持OpenAI兼容接口（Qwen、DeepSeek、ChatGLM等）
"""

import json
import logging
import time
import threading
from typing import Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

# 全局并发控制 - 限制同时最多3个并发请求，避免API限流
_llm_semaphore = threading.Semaphore(3)


class LLMClient:
    """LLM客户端类"""
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化LLM客户端
        
        Args:
            llm_config: LLM配置字典
        """
        self.api_base = llm_config.get('api_base')
        self.api_key = llm_config.get('api_key', 'EMPTY')
        self.model_name = llm_config.get('model_name')
        self.temperature = llm_config.get('temperature', 0.7)
        self.top_p = llm_config.get('top_p', 0.9)
        self.max_tokens = llm_config.get('max_tokens', 4096)
        self.timeout = llm_config.get('timeout', 120)  # 从 60 增加到 120 秒
        self.max_retries = llm_config.get('max_retries', 3)
        
        # 创建OpenAI客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
            timeout=self.timeout
        )
        
    def call_llm(self, prompt: str, expect_json: bool = True) -> Any:
        """
        调用LLM生成内容（带并发控制）
        
        Args:
            prompt: 提示词
            expect_json: 是否期望返回JSON格式
            
        Returns:
            LLM返回的内容（如果expect_json为True则返回解析后的字典）
        """
        with _llm_semaphore:  # 获取信号量，控制并发数
            return self._call_llm_impl(prompt, expect_json)
    
    def _call_llm_impl(self, prompt: str, expect_json: bool = True) -> Any:
        """
        实际的LLM调用实现
        
        Args:
            prompt: 提示词
            expect_json: 是否期望返回JSON格式
            
        Returns:
            LLM返回的内容（如果expect_json为True则返回解析后的字典）
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"调用LLM（第{attempt + 1}次尝试）...")
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "你是一个专业的数据库和SQL专家。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout  # 明确设置超时
                )
                
                content = response.choices[0].message.content.strip()
                logger.info(f"LLM响应成功，长度: {len(content)}")
                
                if expect_json:
                    # 尝试解析JSON
                    return self._extract_json(content)
                else:
                    return content
                    
            except json.JSONDecodeError as e:
                logger.warning(f"JSON解析失败（第{attempt + 1}次）: {str(e)}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避：2, 4, 8秒
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error("JSON解析失败，已达到最大重试次数")
                    raise
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"LLM调用失败（第{attempt + 1}次）: {error_msg}")
                
                # 区分超时和其他错误
                is_timeout = 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower()
                
                if attempt < self.max_retries - 1:
                    # 超时错误使用更长的等待时间
                    wait_time = (3 ** attempt) if is_timeout else (2 ** attempt)
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
        
        raise Exception("LLM调用失败，已达到最大重试次数")
    
    def _extract_json(self, content: str) -> Any:
        """
        从LLM响应中提取JSON
        
        Args:
            content: LLM响应内容
            
        Returns:
            解析后的JSON对象
        """
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取markdown代码块中的JSON
        if '```json' in content:
            start = content.find('```json') + 7
            end = content.find('```', start)
            if end != -1:
                json_str = content[start:end].strip()
                return json.loads(json_str)
        
        # 尝试提取代码块中的内容
        if '```' in content:
            start = content.find('```') + 3
            end = content.find('```', start)
            if end != -1:
                json_str = content[start:end].strip()
                return json.loads(json_str)
        
        # 尝试查找JSON对象或数组
        # 查找第一个 { 或 [
        start_brace = content.find('{')
        start_bracket = content.find('[')
        
        if start_brace == -1 and start_bracket == -1:
            raise json.JSONDecodeError("未找到JSON对象", content, 0)
        
        if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
            # 从 { 开始
            start = start_brace
            # 查找最后一个 }
            end = content.rfind('}')
            if end != -1:
                json_str = content[start:end + 1]
                return json.loads(json_str)
        else:
            # 从 [ 开始
            start = start_bracket
            # 查找最后一个 ]
            end = content.rfind(']')
            if end != -1:
                json_str = content[start:end + 1]
                return json.loads(json_str)
        
        raise json.JSONDecodeError("无法提取有效的JSON", content, 0)


def create_llm_client(llm_config: Dict[str, Any]) -> LLMClient:
    """
    创建LLM客户端的工厂函数
    
    Args:
        llm_config: LLM配置字典
        
    Returns:
        LLMClient实例
    """
    return LLMClient(llm_config)
