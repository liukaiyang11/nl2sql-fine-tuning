"""
日志处理器模块
自定义logging Handler，将日志推送到WebSocket
"""

import logging
import asyncio
from typing import Optional
from .task_manager import task_manager


class WebSocketLogHandler(logging.Handler):
    """WebSocket日志处理器"""
    
    def __init__(self, level=logging.INFO):
        """
        初始化WebSocket日志处理器
        
        Args:
            level: 日志级别
        """
        super().__init__(level)
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        
    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """
        设置事件循环
        
        Args:
            loop: asyncio事件循环
        """
        self.loop = loop
    
    def emit(self, record: logging.LogRecord):
        """
        处理日志记录
        
        Args:
            record: 日志记录
        """
        try:
            # 格式化日志消息
            message = self.format(record)
            
            # 映射日志级别
            level_mapping = {
                logging.DEBUG: "debug",
                logging.INFO: "info",
                logging.WARNING: "warning",
                logging.ERROR: "error",
                logging.CRITICAL: "error"
            }
            level = level_mapping.get(record.levelno, "info")
            
            # 异步添加日志到任务管理器
            if self.loop and self.loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    task_manager.add_log(level, message),
                    self.loop
                )
        except Exception:
            self.handleError(record)


def setup_websocket_logging(logger_name: Optional[str] = None, level=logging.INFO) -> WebSocketLogHandler:
    """
    设置WebSocket日志处理器
    
    Args:
        logger_name: 日志器名称，None表示根日志器
        level: 日志级别
        
    Returns:
        WebSocket日志处理器实例
    """
    # 创建处理器
    ws_handler = WebSocketLogHandler(level)
    
    # 设置格式
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    ws_handler.setFormatter(formatter)
    
    # 添加到日志器
    if logger_name:
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger()
    
    logger.addHandler(ws_handler)
    logger.setLevel(level)
    
    return ws_handler
