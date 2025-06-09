"""
控制台聊天控制器 - FastAPI实现
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
    ProviderInfo, ModelInfo, ChatStatistics
)
from models.schemas.user import UserResponse

# 创建FastAPI路由器
router = APIRouter(prefix="/chat", tags=["Console Chat"])

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

def get_admin_user() -> UserResponse:
    """获取管理员用户（模拟）"""
    from datetime import datetime
    from models.schemas.user import UserRole, UserStatus
    return UserResponse(
        id="admin_123",
        username="admin",
        email="admin@example.com",
        full_name="系统管理员",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

# FastAPI路由定义
@router.post("/test", response_model=BaseResponse[dict])
async def test_chat_endpoint(
    current_user_id: str = Depends(get_current_user_id)
):
    """测试聊天端点"""
    return BaseResponse(
        data={
            "message": "控制台聊天系统测试成功",
            "user_id": current_user_id,
            "endpoint": "console/chat/test",
            "framework": "FastAPI",
            "version": "2.0.0"
        },
        message="测试成功"
    )

@router.post("/messages", response_model=BaseResponse[ChatResponse])
async def send_message(
    request: ChatRequest,
    current_user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service)
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
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # 同步响应
            response = await chat_service.send_message(
                session_id=request.session_id,
                user_id=current_user_id,
                message=request.message,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )

            return BaseResponse(
                data=response,
                message="消息发送成功"
            )
    except Exception as e:
        logging.error(f"Console chat error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送消息失败: {str(e)}"
        )

@router.post("/messages/stream")
async def send_message_stream(
    request: ChatRequest,
    current_user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service)
):
    """发送流式聊天消息"""
    try:
        return StreamingResponse(
            chat_service.send_message_stream(
                session_id=request.session_id,
                user_id=current_user_id,
                message=request.message,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logging.error(f"Console stream chat error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"流式聊天失败: {str(e)}"
        )

@router.post("/messages/regenerate", response_model=BaseResponse[ChatResponse])
async def regenerate_response(
    request: RegenerateRequest,
    current_user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service)
):
    """重新生成回复"""
    try:
        response = await chat_service.regenerate_response(
            session_id=request.session_id,
            user_id=current_user_id,
            message_id=request.message_id
        )

        return BaseResponse(
            data=response,
            message="回复重新生成成功"
        )
    except Exception as e:
        logging.error(f"Console regenerate error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新生成回复失败: {str(e)}"
        )

@router.get("/providers", response_model=BaseResponse[List[ProviderInfo]])
async def get_providers(
    _: UserResponse = Depends(get_admin_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取可用的AI提供商"""
    try:
        providers = await chat_service.get_available_providers()

        return BaseResponse(
            data=providers,
            message="提供商列表获取成功"
        )
    except Exception as e:
        logging.error(f"Console get providers error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取提供商列表失败: {str(e)}"
        )

@router.get("/providers/{provider_name}/models", response_model=BaseResponse[List[ModelInfo]])
async def get_provider_models(
    provider_name: str,
    _: UserResponse = Depends(get_admin_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取指定提供商的模型列表"""
    try:
        models = await chat_service.get_provider_models(provider_name)

        return BaseResponse(
            data=models,
            message=f"提供商 {provider_name} 的模型列表获取成功"
        )
    except Exception as e:
        logging.error(f"Console get models error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型列表失败: {str(e)}"
        )

@router.get("/statistics", response_model=BaseResponse[ChatStatistics])
async def get_chat_statistics(
    _: UserResponse = Depends(get_admin_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取聊天统计信息"""
    try:
        statistics = await chat_service.get_chat_statistics()

        return BaseResponse(
            data=statistics,
            message="聊天统计信息获取成功"
        )
    except Exception as e:
        logging.error(f"Console get statistics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )
