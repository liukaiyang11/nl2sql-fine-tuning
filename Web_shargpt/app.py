#!/usr/bin/env python3
"""
NL2SQL自动化数据生成系统 - FastAPI后端服务器
提供REST API和WebSocket接口，连接前端界面和后端生成模块
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from api.routes import router as api_router
from api.websocket import router as ws_router
from api.download import router as download_router

# 创建FastAPI应用
app = FastAPI(
    title="NL2SQL数据生成系统API",
    description="企业级NL2SQL训练数据自动生成工具API接口",
    version="1.0.0"
)

# 配置CORS - 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix="/api", tags=["API"])
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])
app.include_router(download_router, prefix="/api", tags=["Download"])

# 静态文件服务（前端构建文件）
dist_dir = os.path.join(os.path.dirname(__file__), "dist")
if os.path.exists(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")
    
    @app.get("/")
    async def serve_frontend():
        """服务前端页面"""
        index_file = os.path.join(dist_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "请先构建前端: npm run build"}


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "service": "nl2sql-api",
        "version": "1.0.0"
    }


def main():
    """启动服务器"""
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print("=" * 80)
    print("🚀 NL2SQL数据生成系统API服务器启动")
    print("=" * 80)
    print(f"📍 API地址: http://{host}:{port}/api")
    print(f"📍 WebSocket: ws://{host}:{port}/ws")
    print(f"📍 健康检查: http://{host}:{port}/health")
    print(f"📍 API文档: http://{host}:{port}/docs")
    print("=" * 80)
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,  # 开发模式自动重载
        log_level="info"
    )


if __name__ == "__main__":
    main()
