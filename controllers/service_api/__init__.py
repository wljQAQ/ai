"""
服务API模块 - FastAPI路由器
"""

from fastapi import APIRouter
from .chat import router as chat_router

# 创建服务API主路由器
service_api_router = APIRouter(prefix="/api/service", tags=["Service API"])

# 包含子路由器
service_api_router.include_router(chat_router)

# 健康检查路由
@service_api_router.get("/health")
async def health_check():
    """服务API健康检查"""
    return {
        "status": "healthy",
        "message": "Service API is running",
        "success": True
    }

# 导出路由器
__all__ = ["service_api_router"]
