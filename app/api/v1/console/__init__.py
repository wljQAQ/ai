"""
控制台API路由
"""

from fastapi import APIRouter

from app.api.v1.console.chat import router as chat_router
from app.api.v1.console.session import router as session_router
from app.api.v1.console.workspace import router as workspace_router
from app.api.v1.console.user import router as user_router

# 创建控制台路由
console_router = APIRouter()

# 注册子路由
console_router.include_router(chat_router, prefix="/chat", tags=["Console Chat"])
console_router.include_router(session_router, prefix="/sessions", tags=["Console Sessions"])
console_router.include_router(workspace_router, prefix="/workspace", tags=["Console Workspace"])
console_router.include_router(user_router, prefix="/users", tags=["Console Users"])
