"""
API v1 路由
"""

from fastapi import APIRouter

from app.api.v1.console import console_router
from app.api.v1.web import web_router
from app.api.v1.service import service_router

# 创建主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(console_router, prefix="/console", tags=["Console"])
api_router.include_router(web_router, prefix="/web", tags=["Web"])
api_router.include_router(service_router, prefix="/service", tags=["Service"])
