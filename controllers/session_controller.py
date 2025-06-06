"""
会话控制器 - 处理会话相关的HTTP请求
"""
import logging
from flask import Blueprint
from controllers.base_controller import BaseController
from services.session_service import SessionService
from models.session_model import SessionConfig


class SessionController(BaseController):
    """会话控制器 - 按照MVC规范命名"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def create_session(self):
        """创建新会话"""
        try:
            # 获取并验证请求数据
            data = self.get_json_data(required_fields=["ai_provider", "model"])
            user_id = self.get_user_id()
            
            # 创建会话配置
            config = SessionConfig(
                ai_provider=data["ai_provider"],
                model=data["model"],
                temperature=data.get("temperature", 0.7),
                max_tokens=data.get("max_tokens"),
                system_prompt=data.get("system_prompt"),
                metadata=data.get("metadata", {})
            )
            
            title = data.get("title")
            
            # 获取服务实例
            session_service = self._get_session_service()
            
            # 创建会话
            session = await session_service.create_session(user_id, config, title)
            
            return self.create_response(
                data=session.to_dict(),
                message="Session created successfully",
                status_code=201
            )
        
        except ValueError as e:
            return self.create_error_response(str(e), status_code=400)
        except Exception as e:
            self.logger.error(f"Create session error: {str(e)}")
            return self.create_error_response(
                "Failed to create session",
                status_code=500
            )
    
    async def get_session(self, session_id: str):
        """获取会话详情"""
        try:
            user_id = self.get_user_id()
            
            # 获取服务实例
            session_service = self._get_session_service()
            
            # 获取会话
            session = await session_service.get_session(session_id, user_id)
            if not session:
                return self.create_error_response(
                    "Session not found",
                    status_code=404
                )
            
            return self.create_response(
                data=session.to_dict(),
                message="Session retrieved successfully"
            )
        
        except Exception as e:
            self.logger.error(f"Get session error: {str(e)}")
            return self.create_error_response(
                "Failed to get session",
                status_code=500
            )
    
    async def list_sessions(self):
        """获取会话列表"""
        try:
            user_id = self.get_user_id()
            limit, offset = self.validate_pagination()
            
            # 获取服务实例
            session_service = self._get_session_service()
            
            # 获取会话列表
            sessions = await session_service.list_sessions(user_id, limit, offset)
            
            # 转换为字典格式
            sessions_data = [session.to_dict() for session in sessions]
            
            return self.create_response(
                data={
                    "sessions": sessions_data,
                    "total": len(sessions_data),
                    "limit": limit,
                    "offset": offset
                },
                message="Sessions retrieved successfully"
            )
        
        except ValueError as e:
            return self.create_error_response(str(e), status_code=400)
        except Exception as e:
            self.logger.error(f"List sessions error: {str(e)}")
            return self.create_error_response(
                "Failed to list sessions",
                status_code=500
            )
    
    async def update_session(self, session_id: str):
        """更新会话"""
        try:
            user_id = self.get_user_id()
            data = self.get_json_data()
            
            # 获取服务实例
            session_service = self._get_session_service()
            
            # 更新会话
            success = await session_service.update_session(session_id, user_id, **data)
            if not success:
                return self.create_error_response(
                    "Session not found",
                    status_code=404
                )
            
            return self.create_response(
                message="Session updated successfully"
            )
        
        except ValueError as e:
            return self.create_error_response(str(e), status_code=400)
        except Exception as e:
            self.logger.error(f"Update session error: {str(e)}")
            return self.create_error_response(
                "Failed to update session",
                status_code=500
            )
    
    async def delete_session(self, session_id: str):
        """删除会话"""
        try:
            user_id = self.get_user_id()
            
            # 获取服务实例
            session_service = self._get_session_service()
            
            # 删除会话
            success = await session_service.delete_session(session_id, user_id)
            if not success:
                return self.create_error_response(
                    "Session not found",
                    status_code=404
                )
            
            return self.create_response(
                message="Session deleted successfully"
            )
        
        except Exception as e:
            self.logger.error(f"Delete session error: {str(e)}")
            return self.create_error_response(
                "Failed to delete session",
                status_code=500
            )
    
    async def get_session_messages(self, session_id: str):
        """获取会话消息"""
        try:
            user_id = self.get_user_id()
            limit, offset = self.validate_pagination()
            
            # 获取服务实例
            session_service = self._get_session_service()
            
            # 验证会话权限
            session = await session_service.get_session(session_id, user_id)
            if not session:
                return self.create_error_response(
                    "Session not found",
                    status_code=404
                )
            
            # 获取消息
            messages = await session_service.get_messages(session_id, limit, offset)
            
            # 转换为字典格式
            messages_data = [message.to_dict() for message in messages]
            
            return self.create_response(
                data={
                    "messages": messages_data,
                    "total": len(messages_data),
                    "limit": limit,
                    "offset": offset
                },
                message="Messages retrieved successfully"
            )
        
        except ValueError as e:
            return self.create_error_response(str(e), status_code=400)
        except Exception as e:
            self.logger.error(f"Get session messages error: {str(e)}")
            return self.create_error_response(
                "Failed to get session messages",
                status_code=500
            )
    
    def _get_session_service(self) -> SessionService:
        """获取会话服务实例"""
        # 简化实现：直接创建服务实例
        # 实际项目中应该使用依赖注入
        return SessionService()


# 创建蓝图和控制器实例
session_bp = Blueprint("session", __name__, url_prefix="/sessions")
session_controller = SessionController()


# 注册路由
@session_bp.route("", methods=["POST"])
async def create_session():
    """创建会话路由"""
    return await session_controller.create_session()


@session_bp.route("", methods=["GET"])
async def list_sessions():
    """获取会话列表路由"""
    return await session_controller.list_sessions()


@session_bp.route("/<session_id>", methods=["GET"])
async def get_session(session_id: str):
    """获取会话详情路由"""
    return await session_controller.get_session(session_id)


@session_bp.route("/<session_id>", methods=["PUT"])
async def update_session(session_id: str):
    """更新会话路由"""
    return await session_controller.update_session(session_id)


@session_bp.route("/<session_id>", methods=["DELETE"])
async def delete_session(session_id: str):
    """删除会话路由"""
    return await session_controller.delete_session(session_id)


@session_bp.route("/<session_id>/messages", methods=["GET"])
async def get_session_messages(session_id: str):
    """获取会话消息路由"""
    return await session_controller.get_session_messages(session_id)
