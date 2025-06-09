"""
控制器模块 - FastAPI路由器统一管理
"""

from fastapi import FastAPI
from .console import console_router
from .web import web_router
from .service_api import service_api_router


def init_all_routes(app: FastAPI) -> None:
    """初始化所有路由器"""

    # 注册所有路由器
    app.include_router(console_router)
    app.include_router(web_router)
    app.include_router(service_api_router)
