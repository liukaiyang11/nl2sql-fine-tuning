"""
任务管理器模块
管理NL2SQL生成任务的状态、进度和日志
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStep(str, Enum):
    """任务步骤枚举"""
    CONNECT_DB = "连接数据库"
    EXTRACT_METADATA = "提取元数据"
    GENERATE_CARDS = "生成表卡片"
    PLAN_TOPICS = "规划主题"
    GENERATE_SAMPLES = "生成SQL样本"
    VALIDATE_SQL = "验证SQL"
    EXPORT_DATA = "导出数据"


class TaskManager:
    """任务管理器 - 单例模式"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.current_task_id: Optional[str] = None
        self.task_status: TaskStatus = TaskStatus.IDLE
        self.current_step: int = 0
        self.total_steps: int = 6
        self.step_name: str = ""
        self.progress: int = 0
        self.error_message: str = ""
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # 任务详细信息
        self.task_details: Dict[str, Any] = {}
        
        # 输出文件路径
        self.output_path: str = "./data/nl2sql.jsonl"
        
        # 日志收集
        self.logs: List[Dict[str, Any]] = []
        self.max_logs: int = 1000
    
        # WebSocket连接管理
        self.ws_connections: List[Any] = []
        
        # 进度回调
        self.progress_callbacks: List[Callable] = []
        self.log_callbacks: List[Callable] = []
    
    async def start_task(self, config: Dict[str, Any]) -> str:
        """
        启动新任务
        
        Args:
            config: 任务配置
            
        Returns:
            任务ID
        """
        async with self._lock:
            if self.task_status == TaskStatus.RUNNING:
                raise Exception("已有任务正在运行中")
            
            # 完全重置所有状态字段
            self.current_task_id = str(uuid.uuid4())
            self.task_status = TaskStatus.RUNNING
            self.current_step = 0
            self.progress = 0
            self.step_name = ""
            self.error_message = ""
            self.start_time = datetime.now()
            self.end_time = None
            
            # 清空日志列表，避免旧日志干扰
            self.logs = []
            
            # 清空旧的任务详情
            self.task_details = {}
            
            # 保存输出路径
            if 'generate' in config and 'output_path' in config['generate']:
                self.output_path = config['generate']['output_path']
            
            # 设置新任务详情
            self.task_details = {
                "config": config,
                "samples_generated": 0,
                "samples_valid": 0
            }
            
            await self._broadcast_status()
            return self.current_task_id
    
    async def update_step(self, step: int, step_name: str, details: str = ""):
        """
        更新当前步骤
        
        Args:
            step: 步骤编号 (1-6)
            step_name: 步骤名称
            details: 详细信息
        """
        self.current_step = step
        self.step_name = step_name
        self.progress = int((step / self.total_steps) * 100)
        
        await self.add_log("info", f"开始步骤 {step}/{self.total_steps}: {step_name}")
        
        if details:
            self.task_details["current_details"] = details
        
        await self._broadcast_progress()
    
    async def update_progress(self, progress: int, details: str = ""):
        """
        更新当前步骤的进度
        
        Args:
            progress: 进度百分比 (0-100)
            details: 详细信息
        """
        self.progress = progress
        
        if details:
            self.task_details["current_details"] = details
        
        await self._broadcast_progress()
    
    async def complete_task(self, result: Dict[str, Any]):
        """
        完成任务
        
        Args:
            result: 任务结果
        """
        async with self._lock:
            self.task_status = TaskStatus.COMPLETED
            self.current_step = self.total_steps
            self.progress = 100
            self.end_time = datetime.now()
            self.task_details["result"] = result
            
            duration = (self.end_time - self.start_time).total_seconds()
            await self.add_log("info", f"✅ 任务完成！用时 {duration:.1f} 秒")
            
            await self._broadcast_status()
    
    async def fail_task(self, error: str):
        """
        任务失败
        
        Args:
            error: 错误信息
        """
        async with self._lock:
            self.task_status = TaskStatus.FAILED
            self.error_message = error
            self.end_time = datetime.now()
            
            await self.add_log("error", f"❌ 任务失败: {error}")
            
            await self._broadcast_status()
    
    async def cancel_task(self):
        """取消任务"""
        async with self._lock:
            if self.task_status == TaskStatus.RUNNING:
                self.task_status = TaskStatus.CANCELLED
                self.end_time = datetime.now()
                
                await self.add_log("warning", "⚠️  任务已取消")
                await self._broadcast_status()
    
    async def add_log(self, level: str, message: str):
        """
        添加日志
        
        Args:
            level: 日志级别 (debug, info, warning, error)
            message: 日志消息
        """
        log_entry = {
            "type": "log",
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logs.append(log_entry)
        
        # 限制日志数量
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        
        # 广播日志
        await self._broadcast_log(log_entry)
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "task_id": self.current_task_id,
            "status": self.task_status,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "step_name": self.step_name,
            "progress": self.progress,
            "error_message": self.error_message,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "details": self.task_details
        }
    
    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取日志
        
        Args:
            limit: 返回最近的日志数量
            
        Returns:
            日志列表
        """
        return self.logs[-limit:]
    
    async def add_ws_connection(self, websocket):
        """添加WebSocket连接"""
        if websocket not in self.ws_connections:
            self.ws_connections.append(websocket)
    
    async def remove_ws_connection(self, websocket):
        """移除WebSocket连接"""
        if websocket in self.ws_connections:
            self.ws_connections.remove(websocket)
    
    async def _broadcast_status(self):
        """广播状态更新"""
        message = {
            "type": "status",
            "data": self.get_status()
        }
        await self._broadcast(message)
    
    async def _broadcast_progress(self):
        """广播进度更新"""
        message = {
            "type": "progress",
            "step": self.current_step,
            "total_steps": self.total_steps,
            "step_name": self.step_name,
            "progress": self.progress,
            "details": self.task_details.get("current_details", "")
        }
        await self._broadcast(message)
    
    async def _broadcast_log(self, log_entry: Dict[str, Any]):
        """广播日志"""
        await self._broadcast(log_entry)
    
    async def _broadcast(self, message: Dict[str, Any]):
        """
        向所有WebSocket连接广播消息
        
        Args:
            message: 要广播的消息
        """
        if not self.ws_connections:
            return
        
        # 移除已断开的连接
        disconnected = []
        
        for ws in self.ws_connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        
        # 清理断开的连接
        for ws in disconnected:
            await self.remove_ws_connection(ws)


# 全局任务管理器实例
task_manager = TaskManager()
