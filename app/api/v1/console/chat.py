"""
控制台聊天API
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.deps import (
    get_current_user_id,
    get_admin_user,
    get_chat_service,
    rate_limit_60_per_minute,
    rate_limit_30_per_minute
)
from app.services.chat import ChatService
from app.schemas.base import BaseResponse
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    RegenerateRequest,
    ProviderInfo,
    ModelInfo,
    ChatStatistics
)
from app.schemas.user import UserResponse

router = APIRouter()


@router.post("/messages", response_model=BaseResponse[ChatResponse])
async def send_message(
    request: ChatRequest,
    current_user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service),
    _: None = Depends(rate_limit_60_per_minute)
):
    """
    发送聊天消息
    
    - **session_id**: 会话ID
    - **message**: 用户消息内容
    - **stream**: 是否流式响应
    - **temperature**: 温度参数（可选）
    - **max_tokens**: 最大token数（可选）
    """
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


@router.post("/messages/stream")
async def send_message_stream(
    request: ChatRequest,
    current_user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service),
    _: None = Depends(rate_limit_30_per_minute)
):
    """
    发送流式聊天消息
    
    返回Server-Sent Events格式的流式响应
    """
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


@router.post("/messages/regenerate", response_model=BaseResponse[ChatResponse])
async def regenerate_response(
    request: RegenerateRequest,
    current_user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service),
    _: None = Depends(rate_limit_30_per_minute)
):
    """
    重新生成AI回复
    
    - **session_id**: 会话ID
    - **message_id**: 要重新生成的消息ID（可选）
    """
    response = await chat_service.regenerate_response(
        session_id=request.session_id,
        user_id=current_user_id,
        message_id=request.message_id
    )
    
    return BaseResponse(
        data=response,
        message="回复重新生成成功"
    )


@router.get("/providers", response_model=BaseResponse[List[ProviderInfo]])
async def get_providers(
    current_user: UserResponse = Depends(get_admin_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    获取可用的AI提供商列表
    
    需要管理员权限
    """
    providers = await chat_service.get_available_providers()
    
    return BaseResponse(
        data=providers,
        message="提供商列表获取成功"
    )


@router.get("/providers/{provider_name}/models", response_model=BaseResponse[List[ModelInfo]])
async def get_provider_models(
    provider_name: str,
    current_user: UserResponse = Depends(get_admin_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    获取指定提供商的模型列表
    
    - **provider_name**: 提供商名称
    
    需要管理员权限
    """
    models = await chat_service.get_provider_models(provider_name)
    
    return BaseResponse(
        data=models,
        message=f"提供商 {provider_name} 的模型列表获取成功"
    )


@router.get("/statistics", response_model=BaseResponse[ChatStatistics])
async def get_chat_statistics(
    current_user: UserResponse = Depends(get_admin_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    获取聊天统计信息
    
    需要管理员权限
    """
    statistics = await chat_service.get_chat_statistics()
    
    return BaseResponse(
        data=statistics,
        message="聊天统计信息获取成功"
    )


@router.post("/test", response_model=BaseResponse[dict])
async def test_chat_endpoint(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    测试聊天端点
    """
    return BaseResponse(
        data={
            "message": "控制台聊天API测试成功",
            "user_id": current_user_id,
            "endpoint": "console/chat"
        },
        message="测试成功"
    )
