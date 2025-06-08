"""
Web聊天控制器 - 前端用户聊天功能
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


class WebChatController(BaseController):
    """Web聊天控制器 - 面向前端用户的简化接口"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def send_message(self):
        """发送聊天消息 - Web版本"""
        try:
            data = self.get_json_data(required_fields=["session_id", "message"])
            user_id = self.get_user_id()
            
            session_id = data["session_id"]
            message_content = data["message"]
            stream = data.get("stream", False)
            
            chat_service = self._get_chat_service()
            
            if stream:
                return Response(
                    self._stream_chat_response(
                        chat_service, session_id, user_id, message_content
                    ),
                    mimetype="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",
                    },
                )
            else:
                response = await chat_service.send_message(
                    session_id=session_id,
                    user_id=user_id,
                    message=message_content,
                    stream=False,
                )
                
                return self.create_response(
                    data=response.to_dict(), 
                    message="Message sent successfully"
                )
        
        except ValueError as e:
            return self.create_error_response(str(e), status_code=400)
        except Exception as e:
            self.logger.error(f"Web chat error: {str(e)}")
            return self.create_error_response(
                "Failed to send message", 
                status_code=500
            )
    
    async def stream_message(self):
        """流式发送消息 - Web版本"""
        try:
            data = self.get_json_data(required_fields=["session_id", "message"])
            user_id = self.get_user_id()
            
            session_id = data["session_id"]
            message_content = data["message"]
            
            chat_service = self._get_chat_service()
            
            return Response(
                self._stream_chat_response(chat_service, session_id, user_id, message_content),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        
        except Exception as e:
            self.logger.error(f"Web stream chat error: {str(e)}")
            return self.create_error_response(
                "Failed to start stream", 
                status_code=500
            )
    
    async def regenerate_response(self):
        """重新生成回复 - Web版本"""
        try:
            data = self.get_json_data(required_fields=["session_id"])
            user_id = self.get_user_id()
            session_id = data["session_id"]
            
            chat_service = self._get_chat_service()
            
            response = await chat_service.regenerate_response(
                session_id=session_id, user_id=user_id
            )
            
            return self.create_response(
                data=response.to_dict(), 
                message="Response regenerated successfully"
            )
        
        except ValueError as e:
            return self.create_error_response(str(e), status_code=400)
        except Exception as e:
            self.logger.error(f"Web regenerate error: {str(e)}")
            return self.create_error_response(
                "Failed to regenerate response", 
                status_code=500
            )
    
    async def get_available_models(self):
        """获取可用模型 - Web版本（简化）"""
        try:
            # 返回简化的模型列表，只包含用户需要的信息
            models = [
                {
                    "id": "gpt-3.5-turbo",
                    "name": "GPT-3.5 Turbo",
                    "provider": "openai",
                    "description": "快速响应，适合日常对话"
                },
                {
                    "id": "gpt-4",
                    "name": "GPT-4",
                    "provider": "openai", 
                    "description": "更强大的推理能力，适合复杂任务"
                },
                {
                    "id": "qwen-turbo",
                    "name": "通义千问 Turbo",
                    "provider": "qwen",
                    "description": "阿里云通义千问，中文优化"
                }
            ]
            
            return self.create_response(
                data={"models": models}, 
                message="Available models retrieved successfully"
            )
        
        except Exception as e:
            self.logger.error(f"Web get models error: {str(e)}")
            return self.create_error_response(
                "Failed to get available models", 
                status_code=500
            )
    
    async def _stream_chat_response(self, chat_service, session_id, user_id, message_content):
        """生成流式聊天响应"""
        try:
            async for response in chat_service.send_message_stream(
                session_id=session_id, user_id=user_id, message=message_content
            ):
                yield f"data: {response.to_dict()}\n\n"
            
            yield "data: [DONE]\n\n"
        
        except Exception as e:
            self.logger.error(f"Web stream error: {str(e)}")
            error_response = {
                "success": False,
                "message": str(e),
                "error_code": "STREAM_ERROR",
            }
            yield f"data: {error_response}\n\n"
    
    def _get_chat_service(self) -> ChatService:
        """获取聊天服务实例"""
        # 简化实现：直接创建服务实例
        session_service = SessionService()
        return ChatService(session_service=session_service)


# 创建蓝图和控制器实例
chat_bp = Blueprint("chat", __name__, url_prefix="/chat")
web_chat_controller = WebChatController()


# 注册路由 - Web版本的路由更简洁
@chat_bp.route("/messages", methods=["POST"])
@handle_errors
@require_auth
@rate_limit(limit=30, window=60, per="user")  # Web用户限制更严格
@validate_json(required_fields=["session_id", "message"])
async def send_message():
    """发送消息路由"""
    return await web_chat_controller.send_message()


@chat_bp.route("/messages/stream", methods=["POST"])
@handle_errors
@require_auth
@rate_limit(limit=20, window=60, per="user")  # 流式请求限制更严格
@validate_json(required_fields=["session_id", "message"])
async def stream_message():
    """流式发送消息路由"""
    return await web_chat_controller.stream_message()


@chat_bp.route("/messages/regenerate", methods=["POST"])
@handle_errors
@require_auth
@rate_limit(limit=10, window=60, per="user")  # 重新生成限制最严格
@validate_json(required_fields=["session_id"])
async def regenerate_response():
    """重新生成回复路由"""
    return await web_chat_controller.regenerate_response()


@chat_bp.route("/models", methods=["GET"])
@handle_errors
@require_auth
async def get_available_models():
    """获取可用模型路由"""
    return await web_chat_controller.get_available_models()
