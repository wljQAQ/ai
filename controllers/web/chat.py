"""
Web聊天控制器 - FastAPI实现
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import List

from services.chat_service import ChatService
from services.auth_service import AuthService
from models.schemas.base import BaseResponse
from models.schemas.chat import (
    ChatRequest,
    ChatResponse,
    RegenerateRequest,
    ProviderInfo,
    ModelInfo,
    ChatStatistics,
)
from models.schemas.user import UserResponse

# 创建FastAPI路由器
router = APIRouter(prefix="/chat", tags=["Web API Chat"])


# 依赖注入函数
def get_chat_service() -> ChatService:
    """获取聊天服务实例"""
    return ChatService()


def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    return AuthService()


def get_current_user_id() -> str:
    """获取当前用户ID（模拟）"""
    return "user_123"


@router.post("/messages", response_model=BaseResponse[ChatResponse])
async def send_message(
    request: ChatRequest,
    current_user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service),
):
    """发送聊天消息"""
    try:
        if request.stream:
            # 流式响应
            return StreamingResponse(
                chat_service.send_message_stream(
                    session_id=request.session_id,
                    user_id=current_user_id,
                    message=request.message,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            # 同步响应
            response = await chat_service.send_message(
                session_id=request.session_id,
                user_id=current_user_id,
                message=request.message,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                provider_name=request.provider,
                model=request.model,
            )

            return BaseResponse(data=response, message="消息发送成功")
    except Exception as e:
        logging.error(f"Web chat error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送消息失败: {str(e)}",
        )


@router.get("/models", response_model=BaseResponse[List[dict]])
async def get_available_models(
    current_user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service),
):
    """获取可用模型 - Web版本（简化）"""
    try:
        # 返回简化的模型列表，只包含用户需要的信息
        models = [
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "provider": "openai",
                "description": "快速响应，适合日常对话",
            },
            {
                "id": "gpt-4",
                "name": "GPT-4",
                "provider": "openai",
                "description": "更强大的推理能力，适合复杂任务",
            },
            {
                "id": "qwen-turbo",
                "name": "通义千问 Turbo",
                "provider": "qwen",
                "description": "阿里云通义千问，中文优化",
            },
        ]

        return BaseResponse(data=models, message="可用模型列表获取成功")
    except Exception as e:
        logging.error(f"Web get models error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取可用模型失败: {str(e)}",
        )
