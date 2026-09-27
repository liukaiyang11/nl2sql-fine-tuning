"""
WebSocket处理器模块
提供实时日志和进度推送
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from .task_manager import task_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/logs")
async def websocket_logs(websocket: WebSocket):
    """
    WebSocket端点 - 实时日志推送
    
    Args:
        websocket: WebSocket连接
    """
    await websocket.accept()
    await task_manager.add_ws_connection(websocket)
    
    try:
        # 发送历史日志
        history_logs = task_manager.get_logs(limit=50)
        for log_entry in history_logs:
            await websocket.send_json(log_entry)
        
        # 保持连接，等待客户端断开
        while True:
            # 接收客户端消息（如果有的话）
            data = await websocket.receive_text()
            
            # 可以处理客户端发来的命令
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            elif data == "get_status":
                status = task_manager.get_status()
                await websocket.send_json({"type": "status", "data": status})
            
    except WebSocketDisconnect:
        logger.info("WebSocket客户端断开连接")
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
    finally:
        await task_manager.remove_ws_connection(websocket)


@router.websocket("/progress")
async def websocket_progress(websocket: WebSocket):
    """
    WebSocket端点 - 实时进度推送
    
    Args:
        websocket: WebSocket连接
    """
    await websocket.accept()
    await task_manager.add_ws_connection(websocket)
    
    try:
        # 发送当前状态
        status = task_manager.get_status()
        await websocket.send_json({"type": "status", "data": status})
        
        # 保持连接，等待客户端断开
        while True:
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            elif data == "get_status":
                status = task_manager.get_status()
                await websocket.send_json({"type": "status", "data": status})
            
    except WebSocketDisconnect:
        logger.info("WebSocket客户端断开连接")
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
    finally:
        await task_manager.remove_ws_connection(websocket)


@router.websocket("/all")
async def websocket_all(websocket: WebSocket):
    """
    WebSocket端点 - 推送所有消息（日志+进度）
    
    Args:
        websocket: WebSocket连接
    """
    await websocket.accept()
    await task_manager.add_ws_connection(websocket)
    
    try:
        # 发送当前状态（只在任务运行中时发送，避免发送历史完成状态）
        status = task_manager.get_status()
        if status.get('status') == 'running':
            await websocket.send_json({"type": "status", "data": status})
        
        # 发送历史日志
        history_logs = task_manager.get_logs(limit=50)
        for log_entry in history_logs:
            await websocket.send_json(log_entry)
        
        # 保持连接
        while True:
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            elif data == "get_status":
                status = task_manager.get_status()
                await websocket.send_json({"type": "status", "data": status})
            elif data == "get_logs":
                logs = task_manager.get_logs(limit=100)
                await websocket.send_json({"type": "logs", "data": logs})
            
    except WebSocketDisconnect:
        logger.info("WebSocket客户端断开连接")
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
    finally:
        await task_manager.remove_ws_connection(websocket)

