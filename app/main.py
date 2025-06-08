"""
FastAPI 主应用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings


def create_app() -> FastAPI:
    """创建FastAPI应用"""

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=settings.PROJECT_DESCRIPTION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        debug=settings.DEBUG
    )

    # 设置CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 开发环境允许所有来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 简单的健康检查路由
    @app.get("/")
    async def root():
        """根路径"""
        return {"message": "FastAPI AI Chat System", "version": settings.PROJECT_VERSION}

    @app.get("/health")
    async def health():
        """健康检查"""
        return {"status": "healthy", "version": settings.PROJECT_VERSION}

    # 注册API路由
    from app.api.v1.console.chat import router as console_chat_router
    app.include_router(
        console_chat_router,
        prefix=f"{settings.API_V1_STR}/console/chat",
        tags=["Console Chat"]
    )

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
