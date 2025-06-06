"""
聊天API模块
"""

import asyncio
from flask import Blueprint, request, g, current_app, Response, stream_template
from core.middleware import (
    require_auth,
    validate_json,
    rate_limit,
    create_response,
    handle_errors,
)
# from core.model_providers import ChatRequest, ChatMessage, MessageRole
from services.chat_service import ChatService
from services.session_service import SessionService


chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.route("/test", methods=["POST"])
@handle_errors
@require_auth
@rate_limit(limit=60, window=60, per="user")  # 每分钟60次
@validate_json(required_fields=["session_id", "message"])
async def send_message():
    """发送聊天消息"""
    data = g.json_data
    user_id = g.user_id

    session_id = data["session_id"]
    message_content = data["message"]
    stream = data.get("stream", False)

    try:
        # 获取服务实例
        chat_service = get_chat_service()

        if stream:
            # 流式响应
            return Response(
                stream_chat_response(
                    chat_service, session_id, user_id, message_content
                ),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # 禁用nginx缓冲
                },
            )
        else:
            # 同步响应
            response = await chat_service.send_message(
                session_id=session_id,
                user_id=user_id,
                message=message_content,
                stream=False,
            )

            return create_response(
                data=response.to_dict(), message="Message sent successfully"
            )

    except ValueError as e:
        return create_response(success=False, message=str(e), status_code=400)
    except Exception as e:
        current_app.logger.error(f"Chat error: {str(e)}")
        return create_response(
            success=False, message="Failed to send message", status_code=500
        )


@chat_bp.route("/stream", methods=["POST"])
@handle_errors
@require_auth
@rate_limit(limit=30, window=60, per="user")  # 流式请求限制更严格
@validate_json(required_fields=["session_id", "message"])
async def send_message_stream():
    """发送流式聊天消息"""
    data = g.json_data
    user_id = g.user_id

    session_id = data["session_id"]
    message_content = data["message"]

    try:
        chat_service = get_chat_service()

        return Response(
            stream_chat_response(chat_service, session_id, user_id, message_content),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        current_app.logger.error(f"Stream chat error: {str(e)}")
        return create_response(
            success=False, message="Failed to start stream", status_code=500
        )


@chat_bp.route("/regenerate", methods=["POST"])
@handle_errors
@require_auth
@rate_limit(limit=30, window=60, per="user")
@validate_json(required_fields=["session_id"])
async def regenerate_response():
    """重新生成回复"""
    data = g.json_data
    user_id = g.user_id
    session_id = data["session_id"]

    try:
        chat_service = get_chat_service()

        response = await chat_service.regenerate_response(
            session_id=session_id, user_id=user_id
        )

        return create_response(
            data=response.to_dict(), message="Response regenerated successfully"
        )

    except ValueError as e:
        return create_response(success=False, message=str(e), status_code=400)
    except Exception as e:
        current_app.logger.error(f"Regenerate error: {str(e)}")
        return create_response(
            success=False, message="Failed to regenerate response", status_code=500
        )


@chat_bp.route("/providers", methods=["GET"])
@handle_errors
@require_auth
async def get_providers():
    """获取可用的AI提供商"""
    try:
        chat_service = get_chat_service()
        providers = await chat_service.get_available_providers()

        return create_response(
            data={"providers": providers}, message="Providers retrieved successfully"
        )

    except Exception as e:
        current_app.logger.error(f"Get providers error: {str(e)}")
        return create_response(
            success=False, message="Failed to get providers", status_code=500
        )


@chat_bp.route("/providers/<provider>/models", methods=["GET"])
@handle_errors
@require_auth
async def get_provider_models(provider):
    """获取提供商支持的模型"""
    try:
        chat_service = get_chat_service()
        models = await chat_service.get_provider_models(provider)

        return create_response(
            data={"models": models}, message="Models retrieved successfully"
        )

    except ValueError as e:
        return create_response(success=False, message=str(e), status_code=400)
    except Exception as e:
        current_app.logger.error(f"Get models error: {str(e)}")
        return create_response(
            success=False, message="Failed to get models", status_code=500
        )


async def stream_chat_response(chat_service, session_id, user_id, message_content):
    """生成流式聊天响应"""
    try:
        async for response in chat_service.send_message_stream(
            session_id=session_id, user_id=user_id, message=message_content
        ):
            # 发送SSE格式的数据
            yield f"data: {response.to_dict()}\n\n"

        # 发送结束标记
        yield "data: [DONE]\n\n"

    except Exception as e:
        current_app.logger.error(f"Stream error: {str(e)}")
        error_response = {
            "success": False,
            "message": str(e),
            "error_code": "STREAM_ERROR",
        }
        yield f"data: {error_response}\n\n"


def get_chat_service() -> ChatService:
    """获取聊天服务实例"""
    # 这里应该从依赖注入容器获取服务实例
    # 简化实现，直接创建实例
    from repositories.session_repository import SessionRepository
    from repositories.message_repository import MessageRepository
    from core.extensions import cache_manager, db_manager

    session_repo = SessionRepository(db_manager)
    message_repo = MessageRepository(db_manager)
    session_service = SessionService(session_repo, message_repo, cache_manager)

    return ChatService(
        session_service=session_service,
        adapter_factory=current_app.adapter_factory,
        cache_service=cache_manager,
    )
