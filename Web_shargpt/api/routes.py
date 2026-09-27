"""
REST API路由模块
提供数据库测试、LLM测试、任务启动等API
"""

import os
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from modules.db_connector import create_connector
from modules.llm_client import create_llm_client
from .task_manager import task_manager
from .log_handler import setup_websocket_logging

logger = logging.getLogger(__name__)
router = APIRouter()


# 请求模型
class DatabaseConfig(BaseModel):
    """数据库配置"""
    type: str = "mysql"
    host: str
    port: int = 3306
    user: str
    password: str
    database: str


class LLMConfig(BaseModel):
    """LLM配置"""
    api_base: str
    api_key: str
    model_name: str
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 4096
    timeout: int = 60
    max_retries: int = 3


class GenerateConfig(BaseModel):
    """生成配置"""
    total_samples: int = 100
    dialect: str = "mysql"
    output_path: str = "./data/nl2sql.jsonl"
    output_format: str = "alpaca"
    enable_validation: bool = True
    min_tables_per_topic: int = 3
    max_tables_per_topic: int = 8


class TaskConfig(BaseModel):
    """任务配置"""
    db: DatabaseConfig
    llm: LLMConfig
    generate: GenerateConfig


# API端点
@router.post("/test-db-connection")
async def test_db_connection(config: DatabaseConfig):
    """
    测试数据库连接
    
    Args:
        config: 数据库配置
        
    Returns:
        连接测试结果
    """
    try:
        logger.info(f"测试数据库连接: {config.host}:{config.port}/{config.database}")
        
        # 创建数据库连接器
        db_config = config.model_dump()
        connector = create_connector(db_config)
        
        # 尝试连接
        conn = connector.get_connection()
        
        # 获取表数量
        if db_config['type'] == 'mysql':
            result = connector.execute_query(
                f"SELECT COUNT(*) as count FROM information_schema.TABLES WHERE TABLE_SCHEMA = '{db_config['database']}'"
            )
            tables_count = result[0]['count'] if result else 0
        else:
            tables_count = 0
        
        connector.close()
        
        return {
            "success": True,
            "message": "数据库连接成功",
            "tables_count": tables_count
        }
        
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"数据库连接失败: {str(e)}")


@router.post("/test-llm-connection")
async def test_llm_connection(config: LLMConfig):
    """
    测试LLM连接
    
    Args:
        config: LLM配置
        
    Returns:
        连接测试结果
    """
    try:
        logger.info(f"测试LLM连接: {config.api_base}")
        
        # 创建LLM客户端
        llm_config = config.model_dump()
        client = create_llm_client(llm_config)
        
        # 发送测试请求
        response = client.call_llm("你好，请回复'连接成功'", expect_json=False)
        
        return {
            "success": True,
            "message": "LLM连接成功",
            "response": response[:100] if len(response) > 100 else response
        }
        
    except Exception as e:
        logger.error(f"LLM连接失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"LLM连接失败: {str(e)}")


@router.post("/start-generation")
async def start_generation(config: TaskConfig):
    """
    启动生成任务
    
    Args:
        config: 任务配置
        
    Returns:
        任务ID和状态
    """
    try:
        # 检查是否已有任务在运行
        status = task_manager.get_status()
        if status['status'] == 'running':
            raise HTTPException(status_code=400, detail="已有任务正在运行中")
        
        # 启动任务
        task_id = await task_manager.start_task(config.model_dump())
        
        # 在后台运行生成任务
        asyncio.create_task(run_generation_task(config))
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "任务已启动"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动任务失败: {str(e)}")


@router.get("/status")
async def get_status():
    """
    获取当前任务状态
    
    Returns:
        任务状态信息
    """
    return task_manager.get_status()


@router.get("/logs")
async def get_logs(limit: int = 100):
    """
    获取日志
    
    Args:
        limit: 返回的日志数量
        
    Returns:
        日志列表
    """
    return {
        "logs": task_manager.get_logs(limit=limit)
    }


@router.post("/cancel")
async def cancel_task():
    """
    取消当前任务
    
    Returns:
        取消结果
    """
    try:
        await task_manager.cancel_task()
        return {
            "success": True,
            "message": "任务已取消"
        }
    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


# 后台任务函数
async def run_generation_task(config: TaskConfig):
    """
    运行生成任务（后台）
    
    Args:
        config: 任务配置
    """
    try:
        # 设置日志处理器
        ws_handler = setup_websocket_logging(level=logging.INFO)
        ws_handler.set_event_loop(asyncio.get_event_loop())
        
        # 为各个模块的 logger 添加 handler，确保所有模块日志都能实时推送
        for module_name in ['modules.generator', 'modules.llm_client', 'modules.validator', 
                            'modules.metadata_extractor', 'modules.planner', 'modules.table_cards']:
            module_logger = logging.getLogger(module_name)
            module_logger.addHandler(ws_handler)
            module_logger.setLevel(logging.INFO)
        
        # 导入生成模块
        from modules.db_connector import create_connector
        from modules.metadata_extractor import extract_and_save_metadata
        from modules.table_cards import generate_and_save_table_cards
        from modules.planner import generate_and_save_plan
        from modules.generator import generate_and_save_samples
        from modules.validator import validate_and_save_samples
        from modules.exporter import export_samples
        
        # 步骤1: 连接数据库
        await task_manager.update_step(1, "连接数据库", "正在连接数据库...")
        db_connector = create_connector(config.db.model_dump())
        db_connector.get_connection()
        await asyncio.sleep(0.5)  # 短暂延迟以显示进度
        
        # 步骤2: 提取元数据
        await task_manager.update_step(2, "提取元数据", "正在提取数据库表结构...")
        metadata_path = os.path.join("./data", "metadata.json")
        # 在线程池中执行同步函数，避免阻塞事件循环
        metadata = await asyncio.to_thread(extract_and_save_metadata, db_connector, metadata_path)
        
        if not metadata:
            raise Exception("未提取到任何表元数据")
        
        await task_manager.add_log("info", f"成功提取 {len(metadata)} 个表的元数据")
        
        # 步骤3: 生成表卡片
        await task_manager.update_step(3, "生成表卡片", "正在生成表卡片摘要...")
        table_cards_path = os.path.join("./data", "table_cards.json")
        # 在线程池中执行同步函数，避免阻塞事件循环
        table_cards = await asyncio.to_thread(generate_and_save_table_cards, metadata, table_cards_path)
        await task_manager.add_log("info", f"成功生成 {len(table_cards)} 个表卡片")
        
        # 步骤4: 规划主题（LLM阶段A）
        await task_manager.update_step(4, "规划主题", "正在调用LLM生成主题规划...")
        llm_client = create_llm_client(config.llm.model_dump())
        plan_path = os.path.join("./data", "plan.json")
        # 在线程池中执行同步函数，避免阻塞事件循环
        plan = await asyncio.to_thread(
            generate_and_save_plan,
            llm_client,
            table_cards,
            config.generate.total_samples,
            plan_path,
            config.generate.min_tables_per_topic,
            config.generate.max_tables_per_topic,
            config.generate.dialect
        )
        await task_manager.add_log("info", f"成功生成规划，包含 {len(plan['topics'])} 个主题")
        
        # 步骤5: 生成样本（LLM阶段B）
        await task_manager.update_step(5, "生成SQL样本", "正在生成NL2SQL样本...")
        samples_raw_path = os.path.join("./data", "samples_raw.jsonl")
        # 在线程池中执行同步函数，避免阻塞事件循环
        samples = await asyncio.to_thread(
            generate_and_save_samples,
            llm_client,
            metadata,
            plan,
            samples_raw_path,
            config.generate.dialect
        )
        
        if not samples:
            raise Exception("未生成任何样本")
        
        await task_manager.add_log("info", f"成功生成 {len(samples)} 条样本")
        
        # 更新任务详情
        task_manager.task_details["samples_generated"] = len(samples)
        
        # 步骤6: 验证SQL
        if config.generate.enable_validation:
            await task_manager.update_step(6, "验证SQL", "正在验证SQL语法和Schema...")
            samples_valid_path = os.path.join("./data", "samples_valid.jsonl")
            # 在线程池中执行同步函数，避免阻塞事件循环
            valid_samples = await asyncio.to_thread(
                validate_and_save_samples,
                samples,
                metadata,
                samples_valid_path,
                config.generate.dialect
            )
        else:
            await task_manager.add_log("info", "跳过SQL验证步骤")
            valid_samples = samples
        
        if not valid_samples:
            raise Exception("没有有效样本")
        
        await task_manager.add_log("info", f"验证完成，有效样本: {len(valid_samples)} 条")
        
        # 更新任务详情
        task_manager.task_details["samples_valid"] = len(valid_samples)
        
        # 导出训练数据
        await task_manager.update_step(6, "导出数据", "正在导出训练数据...")
        # 在线程池中执行同步函数，避免阻塞事件循环
        await asyncio.to_thread(
            export_samples,
            valid_samples,
            config.generate.output_path,
            config.generate.output_format
        )
        
        # 完成任务
        result = {
            "total_samples": len(samples),
            "valid_samples": len(valid_samples),
            "output_path": config.generate.output_path,
            "output_format": config.generate.output_format
        }
        
        await task_manager.complete_task(result)
        
        # 关闭数据库连接
        db_connector.close()
        
    except Exception as e:
        logger.error(f"任务执行失败: {str(e)}", exc_info=True)
        await task_manager.fail_task(str(e))

