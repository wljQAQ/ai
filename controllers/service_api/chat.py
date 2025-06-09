"""
服务API聊天控制器 - FastAPI实现
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import List

from services.chat_service import ChatService
from services.auth_service import AuthService
from models.schemas.base import BaseResponse
from models.schemas.chat import (
    ChatRequest, ChatResponse, RegenerateRequest,
    SimpleChatRequest, SimpleChatResponse
)

# 创建FastAPI路由器
router = APIRouter(prefix="/chat", tags=["Service API Chat"])

# 依赖注入函数
def get_chat_service() -> ChatService:
    """获取聊天服务实例"""
    return ChatService()

def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    return AuthService()

def get_api_key() -> str:
    """获取API密钥（模拟）"""
    return "api_key_123"

# FastAPI路由定义
@router.post("/test", response_model=BaseResponse[dict])
async def test_service_api_endpoint(
    api_key: str = Depends(get_api_key)
):
    """测试服务API端点"""
    return BaseResponse(
        data={
            "message": "服务API聊天系统测试成功",
            "api_key": api_key,
            "endpoint": "service/chat/test",
            "framework": "FastAPI",
            "version": "2.0.0"
        },
        message="测试成功"
    )

@router.post("/simple", response_model=BaseResponse[SimpleChatResponse])
async def simple_chat(
    request: SimpleChatRequest,
    api_key: str = Depends(get_api_key),
    chat_service: ChatService = Depends(get_chat_service)
):
    """简化聊天接口 - 第三方服务调用"""
    try:
        # 如果没有提供session_id，创建一个新的
        session_id = request.session_id or f"api_session_{api_key}_{hash(request.message) % 10000}"

        # 发送消息
        response = await chat_service.send_message(
            session_id=session_id,
            user_id=f"api_user_{api_key}",
            message=request.message,
            stream=request.stream
        )

        # 转换为简化响应
        simple_response = SimpleChatResponse(
            session_id=session_id,
            message=response.content,
            model=response.model,
            created_at=response.created_at
        )

        return BaseResponse(
            data=simple_response,
            message="聊天成功"
        )
    except Exception as e:
        logging.error(f"Service API chat error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天失败: {str(e)}"
        )

@router.get("/health", response_model=BaseResponse[dict])
async def health_check(
    api_key: str = Depends(get_api_key)
):
    """服务API健康检查"""
    return BaseResponse(
        data={
            "status": "healthy",
            "api_key": api_key,
            "service": "chat_api",
            "version": "2.0.0"
        },
        message="服务正常"
    )
