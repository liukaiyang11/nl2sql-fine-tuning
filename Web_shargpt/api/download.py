"""
文件下载模块
提供生成数据的下载功能
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/download/latest")
async def download_latest():
    """
    下载最新生成的训练数据
    
    Returns:
        最新的nl2sql.jsonl文件
    """
    # 尝试从任务管理器获取输出路径
    try:
        from .task_manager import TaskManager
        task_manager = TaskManager()
        file_path = task_manager.output_path
    except:
        # 如果失败，使用默认路径
        file_path = "./data/nl2sql.jsonl"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"训练数据文件不存在: {file_path}，请先生成数据")
    
    # 从路径中提取文件名
    filename = os.path.basename(file_path)
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/jsonl"
    )


@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    下载生成的数据文件
    
    Args:
        filename: 文件名
        
    Returns:
        文件下载响应
    """
    # 安全检查：只允许下载data目录下的特定文件
    allowed_files = [
        "metadata.json",
        "table_cards.json", 
        "plan.json",
        "samples_raw.jsonl",
        "samples_valid.jsonl",
        "nl2sql.jsonl",
        "nl2sql_alpaca.jsonl",
        "nl2sql_sharegpt.jsonl"
    ]
    
    if filename not in allowed_files:
        raise HTTPException(status_code=403, detail="不允许下载此文件")
    
    file_path = os.path.join("./data", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 根据文件扩展名设置正确的 media type
    media_type = "application/octet-stream"
    if filename.endswith(".jsonl"):
        media_type = "application/jsonl"
    elif filename.endswith(".json"):
        media_type = "application/json"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )

