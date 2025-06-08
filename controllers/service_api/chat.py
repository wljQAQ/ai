"""
服务API聊天控制器 - 第三方集成聊天功能
"""

import logging
from flask import Blueprint, Response
from controllers.base_controller import BaseController
from services.chat_service import ChatService
from services.session_service import SessionService
from core.middleware import (
    require_auth,
    validate_json,
    rate_limit,
    handle_errors,
)


class ServiceApiChatController(BaseController):
    """服务API聊天控制器 - 面向第三方集成的API接口"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def chat_completions(self):
        """聊天完成接口 - 兼容OpenAI API格式"""
        try:
            data = self.get_json_data(required_fields=["messages"])
            user_id = self.get_user_id()
            
            messages = data["messages"]
            model = data.get("model", "gpt-3.5-turbo")
            temperature = data.get("temperature", 0.7)
            max_tokens = data.get("max_tokens", 2000)
            stream = data.get("stream", False)
            
            # 创建临时会话或使用现有会话
            session_id = data.get("session_id")
            if not session_id:
                # 创建临时会话
                from models.session_model import SessionConfig
                config = SessionConfig(
                    ai_provider="openai",  # 默认使用OpenAI
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                session_service = self._get_session_service()
                session = await session_service.create_session(user_id, config, "API Session")
                session_id = session.id
            
            chat_service = self._get_chat_service()
            
            if stream:
                return Response(
                    self._stream_chat_completions(
                        chat_service, session_id, user_id, messages[-1]["content"]
                    ),
                    mimetype="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                    },
                )
            else:
                response = await chat_service.send_message(
                    session_id=session_id,
                    user_id=user_id,
                    message=messages[-1]["content"],
                    stream=False,
                )
                
                # 返回OpenAI兼容格式
                openai_response = {
                    "id": f"chatcmpl-{response.id}",
                    "object": "chat.completion",
                    "created": int(response.created_at.timestamp()),
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": response.content
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": response.prompt_tokens or 0,
                        "completion_tokens": response.completion_tokens or 0,
                        "total_tokens": (response.prompt_tokens or 0) + (response.completion_tokens or 0)
                    }
                }
                
                return self.create_response(
                    data=openai_response,
                    message="Chat completion successful"
                )
        
        except ValueError as e:
            return self.create_error_response(str(e), status_code=400)
        except Exception as e:
            self.logger.error(f"Service API chat error: {str(e)}")
            return self.create_error_response(
                "Failed to process chat completion", 
                status_code=500
            )
    
    async def simple_chat(self):
        """简单聊天接口 - 简化的API格式"""
        try:
            data = self.get_json_data(required_fields=["message"])
            user_id = self.get_user_id()
            
            message = data["message"]
            session_id = data.get("session_id")
            model = data.get("model", "gpt-3.5-turbo")
            
            # 如果没有提供session_id，创建临时会话
            if not session_id:
                from models.session_model import SessionConfig
                config = SessionConfig(
                    ai_provider="openai",
                    model=model,
                    temperature=0.7
                )
                session_service = self._get_session_service()
                session = await session_service.create_session(user_id, config, "API Session")
                session_id = session.id
            
            chat_service = self._get_chat_service()
            response = await chat_service.send_message(
                session_id=session_id,
                user_id=user_id,
                message=message,
                stream=False,
            )
            
            # 返回简化格式
            simple_response = {
                "session_id": session_id,
                "message": response.content,
                "model": model,
                "created_at": response.created_at.isoformat()
            }
            
            return self.create_response(
                data=simple_response,
                message="Message sent successfully"
            )
        
        except ValueError as e:
            return self.create_error_response(str(e), status_code=400)
        except Exception as e:
            self.logger.error(f"Service API simple chat error: {str(e)}")
            return self.create_error_response(
                "Failed to send message", 
                status_code=500
            )
    
    async def _stream_chat_completions(self, chat_service, session_id, user_id, message):
        """生成流式聊天完成响应 - OpenAI兼容格式"""
        try:
            async for response in chat_service.send_message_stream(
                session_id=session_id, user_id=user_id, message=message
            ):
                # 转换为OpenAI流式格式
                chunk = {
                    "id": f"chatcmpl-{response.id}",
                    "object": "chat.completion.chunk",
                    "created": int(response.created_at.timestamp()),
                    "model": "gpt-3.5-turbo",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "content": response.content
                            },
                            "finish_reason": None
                        }
                    ]
                }
                yield f"data: {chunk}\n\n"
            
            # 发送结束标记
            final_chunk = {
                "id": f"chatcmpl-{response.id}",
                "object": "chat.completion.chunk",
                "created": int(response.created_at.timestamp()),
                "model": "gpt-3.5-turbo",
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }
                ]
            }
            yield f"data: {final_chunk}\n\n"
            yield "data: [DONE]\n\n"
        
        except Exception as e:
            self.logger.error(f"Service API stream error: {str(e)}")
            error_chunk = {
                "error": {
                    "message": str(e),
                    "type": "server_error"
                }
            }
            yield f"data: {error_chunk}\n\n"
    
    def _get_chat_service(self) -> ChatService:
        """获取聊天服务实例"""
        session_service = SessionService()
        return ChatService(session_service=session_service)
    
    def _get_session_service(self) -> SessionService:
        """获取会话服务实例"""
        return SessionService()


# 创建蓝图和控制器实例
chat_bp = Blueprint("chat", __name__, url_prefix="/chat")
service_api_chat_controller = ServiceApiChatController()


# 注册路由 - 服务API版本
@chat_bp.route("/completions", methods=["POST"])
@handle_errors
@require_auth
@rate_limit(limit=100, window=60, per="user")  # 第三方API限制相对宽松
@validate_json(required_fields=["messages"])
async def chat_completions():
    """聊天完成接口 - OpenAI兼容"""
    return await service_api_chat_controller.chat_completions()


@chat_bp.route("/simple", methods=["POST"])
@handle_errors
@require_auth
@rate_limit(limit=100, window=60, per="user")
@validate_json(required_fields=["message"])
async def simple_chat():
    """简单聊天接口"""
    return await service_api_chat_controller.simple_chat()
