"""
控制台API模块 - FastAPI路由器
"""

from fastapi import APIRouter
from .chat import router as chat_router
from .session import router as session_router
from .workspace import router as workspace_router

# 创建控制台主路由器
console_router = APIRouter(prefix="/api/console", tags=["Console API"])

# 包含子路由器
console_router.include_router(chat_router)
console_router.include_router(session_router)
console_router.include_router(workspace_router)

# 健康检查路由
@console_router.get("/health")
async def health_check():
    """控制台API健康检查"""
    return {
        "status": "healthy",
        "message": "Console API is running",
        "success": True
    }

# 导出路由器
__all__ = ["console_router"]
