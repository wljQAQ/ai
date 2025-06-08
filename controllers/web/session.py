"""
Web会话控制器 - 前端用户会话管理功能
"""

import logging
from flask import Blueprint
from controllers.base_controller import BaseController
from services.session_service import SessionService
from models.session_model import SessionConfig
from core.middleware import (
    require_auth,
    validate_json,
    rate_limit,
    handle_errors,
)


class WebSessionController(BaseController):
    """Web会话控制器 - 面向前端用户的简化接口"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def create_session(self):
        """创建新会话 - Web版本"""
        try:
            data = self.get_json_data()
            user_id = self.get_user_id()
            
            # Web版本使用默认配置，简化用户操作
            ai_provider = data.get("ai_provider", "openai")
            model = data.get("model", "gpt-3.5-turbo")
            title = data.get("title", "新的聊天")
            
            config = SessionConfig(
                ai_provider=ai_provider,
                model=model,
                temperature=data.get("temperature", 0.7),
                max_tokens=data.get("max_tokens", 2000),
                system_prompt=data.get("system_prompt"),
                metadata=data.get("metadata", {})
            )
            
            session_service = self._get_session_service()
            session = await session_service.create_session(user_id, config, title)
            
            return self.create_response(
                data=session.to_dict(),
                message="Session created successfully",
                status_code=201
            )
        
        except ValueError as e:
            return self.create_error_response(str(e), status_code=400)
        except Exception as e:
            self.logger.error(f"Web create session error: {str(e)}")
            return self.create_error_response(
                "Failed to create session",
                status_code=500
            )
    
    async def list_sessions(self):
        """获取会话列表 - Web版本"""
        try:
            user_id = self.get_user_id()
            limit, offset = self.validate_pagination(limit=10)  # Web版本默认更少
            
            session_service = self._get_session_service()
            sessions = await session_service.list_sessions(user_id, limit, offset)
            
            # 简化会话信息，只返回前端需要的字段
            sessions_data = []
            for session in sessions:
                session_dict = session.to_dict()
                simplified_session = {
                    "id": session_dict["id"],
                    "title": session_dict["title"],
                    "ai_provider": session_dict["config"]["ai_provider"],
                    "model": session_dict["config"]["model"],
                    "created_at": session_dict["created_at"],
                    "updated_at": session_dict["updated_at"],
                    "message_count": session_dict.get("message_count", 0)
                }
                sessions_data.append(simplified_session)
            
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
            self.logger.error(f"Web list sessions error: {str(e)}")
            return self.create_error_response(
                "Failed to list sessions",
                status_code=500
            )
    
    async def get_session(self, session_id: str):
        """获取会话详情 - Web版本"""
        try:
            user_id = self.get_user_id()
            session_service = self._get_session_service()
            
            session = await session_service.get_session(session_id, user_id)
            if not session:
                return self.create_error_response(
                    "Session not found",
                    status_code=404
                )
            
            # 简化会话信息
            session_dict = session.to_dict()
            simplified_session = {
                "id": session_dict["id"],
                "title": session_dict["title"],
                "ai_provider": session_dict["config"]["ai_provider"],
                "model": session_dict["config"]["model"],
                "temperature": session_dict["config"]["temperature"],
                "system_prompt": session_dict["config"].get("system_prompt"),
                "created_at": session_dict["created_at"],
                "updated_at": session_dict["updated_at"]
            }
            
            return self.create_response(
                data=simplified_session,
                message="Session retrieved successfully"
            )
        
        except Exception as e:
            self.logger.error(f"Web get session error: {str(e)}")
            return self.create_error_response(
                "Failed to get session",
                status_code=500
            )
    
    async def update_session(self, session_id: str):
        """更新会话 - Web版本（只允许更新标题）"""
        try:
            user_id = self.get_user_id()
            data = self.get_json_data()
            
            # Web版本只允许更新标题，防止用户误操作
            allowed_fields = ["title"]
            update_data = {k: v for k, v in data.items() if k in allowed_fields}
            
            if not update_data:
                return self.create_error_response(
                    "No valid fields to update",
                    status_code=400
                )
            
            session_service = self._get_session_service()
            success = await session_service.update_session(session_id, user_id, **update_data)
            
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
            self.logger.error(f"Web update session error: {str(e)}")
            return self.create_error_response(
                "Failed to update session",
                status_code=500
            )
    
    async def delete_session(self, session_id: str):
        """删除会话 - Web版本"""
        try:
            user_id = self.get_user_id()
            session_service = self._get_session_service()
            
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
            self.logger.error(f"Web delete session error: {str(e)}")
            return self.create_error_response(
                "Failed to delete session",
                status_code=500
            )
    
    def _get_session_service(self) -> SessionService:
        """获取会话服务实例"""
        return SessionService()


# 创建蓝图和控制器实例
session_bp = Blueprint("session", __name__, url_prefix="/sessions")
web_session_controller = WebSessionController()


# 注册路由 - Web版本的路由
@session_bp.route("", methods=["POST"])
@handle_errors
@require_auth
@rate_limit(limit=20, window=60, per="user")  # Web用户创建会话限制
async def create_session():
    """创建会话路由"""
    return await web_session_controller.create_session()


@session_bp.route("", methods=["GET"])
@handle_errors
@require_auth
async def list_sessions():
    """获取会话列表路由"""
    return await web_session_controller.list_sessions()


@session_bp.route("/<session_id>", methods=["GET"])
@handle_errors
@require_auth
async def get_session(session_id: str):
    """获取会话详情路由"""
    return await web_session_controller.get_session(session_id)


@session_bp.route("/<session_id>", methods=["PUT"])
@handle_errors
@require_auth
@rate_limit(limit=30, window=60, per="user")
async def update_session(session_id: str):
    """更新会话路由"""
    return await web_session_controller.update_session(session_id)


@session_bp.route("/<session_id>", methods=["DELETE"])
@handle_errors
@require_auth
@rate_limit(limit=10, window=60, per="user")  # 删除操作限制更严格
async def delete_session(session_id: str):
    """删除会话路由"""
    return await web_session_controller.delete_session(session_id)
