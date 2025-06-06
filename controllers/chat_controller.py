"""
聊天控制器 - 处理聊天相关的HTTP请求
"""
import asyncio
import logging
from flask import Blueprint, Response, current_app, stream_template
from controllers.base_controller import BaseController
from services.chat_service import ChatService
from services.session_service import SessionService
from core.model_providers import provider_registry


class ChatController(BaseController):
    """聊天控制器 - 按照MVC规范命名"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def send_message(self):
        """发送聊天消息"""
        try:
            # 获取并验证请求数据
            data = self.get_json_data(required_fields=["session_id", "message"])
            user_id = self.get_user_id()
            
            session_id = data["session_id"]
            message_content = data["message"]
            stream = data.get("stream", False)
            
            # 获取服务实例
            chat_service = self._get_chat_service()
            
            if stream:
                # 流式响应
                return Response(
                    self._stream_chat_response(
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
                
                return self.create_response(
                    data=response.to_dict(), 
                    message="Message sent successfully"
                )
        
        except ValueError as e:
            return self.create_error_response(str(e), status_code=400)
        except Exception as e:
            self.logger.error(f"Chat error: {str(e)}")
            return self.create_error_response(
                "Failed to send message", 
                status_code=500
            )
    
    async def send_message_stream(self):
        """发送流式聊天消息"""
        try:
            # 获取并验证请求数据
            data = self.get_json_data(required_fields=["session_id", "message"])
            user_id = self.get_user_id()
            
            session_id = data["session_id"]
            message_content = data["message"]
            
            # 获取服务实例
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
            self.logger.error(f"Stream chat error: {str(e)}")
            return self.create_error_response(
                "Failed to start stream", 
                status_code=500
            )
    
    async def regenerate_response(self):
        """重新生成回复"""
        try:
            # 获取并验证请求数据
            data = self.get_json_data(required_fields=["session_id"])
            user_id = self.get_user_id()
            session_id = data["session_id"]
            
            # 获取服务实例
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
            self.logger.error(f"Regenerate error: {str(e)}")
            return self.create_error_response(
                "Failed to regenerate response", 
                status_code=500
            )
    
    async def get_providers(self):
        """获取可用的AI提供商"""
        try:
            chat_service = self._get_chat_service()
            providers = await chat_service.get_available_providers()
            
            # 转换为字典格式
            providers_data = [provider.to_dict() for provider in providers]
            
            return self.create_response(
                data={"providers": providers_data}, 
                message="Providers retrieved successfully"
            )
        
        except Exception as e:
            self.logger.error(f"Get providers error: {str(e)}")
            return self.create_error_response(
                "Failed to get providers", 
                status_code=500
            )
    
    async def get_provider_models(self, provider_name: str):
        """获取提供商支持的模型"""
        try:
            chat_service = self._get_chat_service()
            models = await chat_service.get_provider_models(provider_name)
            
            return self.create_response(
                data={"models": models}, 
                message="Models retrieved successfully"
            )
        
        except ValueError as e:
            return self.create_error_response(str(e), status_code=400)
        except Exception as e:
            self.logger.error(f"Get models error: {str(e)}")
            return self.create_error_response(
                "Failed to get models", 
                status_code=500
            )
    
    def test(self):
        """测试端点"""
        return self.create_response(
            data={"message": "Chat controller test endpoint working"},
            message="Test successful"
        )
    
    async def _stream_chat_response(self, chat_service, session_id, user_id, message_content):
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
            self.logger.error(f"Stream error: {str(e)}")
            error_response = {
                "success": False,
                "message": str(e),
                "error_code": "STREAM_ERROR",
            }
            yield f"data: {error_response}\n\n"
    
    def _get_chat_service(self) -> ChatService:
        """获取聊天服务实例"""
        # 简化实现：直接创建服务实例
        # 实际项目中应该使用依赖注入
        session_service = SessionService()
        return ChatService(session_service, provider_registry)


# 创建蓝图和控制器实例
chat_bp = Blueprint("chat", __name__, url_prefix="/chat")
chat_controller = ChatController()


# 注册路由
@chat_bp.route("/test", methods=["POST"])
def test():
    """测试路由"""
    return chat_controller.test()


@chat_bp.route("/send", methods=["POST"])
async def send_message():
    """发送消息路由"""
    return await chat_controller.send_message()


@chat_bp.route("/stream", methods=["POST"])
async def send_message_stream():
    """流式发送消息路由"""
    return await chat_controller.send_message_stream()


@chat_bp.route("/regenerate", methods=["POST"])
async def regenerate_response():
    """重新生成回复路由"""
    return await chat_controller.regenerate_response()


@chat_bp.route("/providers", methods=["GET"])
async def get_providers():
    """获取提供商路由"""
    return await chat_controller.get_providers()


@chat_bp.route("/providers/<provider_name>/models", methods=["GET"])
async def get_provider_models(provider_name: str):
    """获取提供商模型路由"""
    return await chat_controller.get_provider_models(provider_name)
