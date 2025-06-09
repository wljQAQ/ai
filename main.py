"""
统一AI聊天系统启动文件 - 支持Flask和FastAPI双模式
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入统一的schemas
from models.schemas.base import BaseResponse, HealthCheck, HealthStatus

# 导入控制器统一初始化
from controllers import init_all_routes

# 创建FastAPI应用
app = FastAPI(
    title="AI Chat System",
    version="2.0.0",
    description="统一AI聊天系统 - MVC架构重构版",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化所有控制器路由器
init_all_routes(app)


# 注意：聊天相关路由已迁移到 controllers/console/chat.py

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True, log_level="info")
