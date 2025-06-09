"""
Web API模块 - FastAPI路由器
"""

from fastapi import APIRouter
from .chat import router as chat_router

# 创建Web主路由器
web_router = APIRouter(prefix="/api/web", tags=["Web API"])

# 包含子路由器
web_router.include_router(chat_router)
