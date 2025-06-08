"""
FastAPI AI聊天系统启动文件
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 创建简化的FastAPI应用
app = FastAPI(
    title="AI Chat System",
    version="2.0.0",
    description="统一AI聊天系统 - FastAPI版本",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 基础路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "FastAPI AI Chat System",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": "ai-chat-system"
    }

# 简单的聊天测试端点
@app.post("/api/v1/console/chat/test")
async def test_chat():
    """测试聊天端点"""
    return {
        "success": True,
        "message": "FastAPI聊天系统测试成功",
        "data": {
            "endpoint": "console/chat/test",
            "framework": "FastAPI",
            "version": "2.0.0"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
