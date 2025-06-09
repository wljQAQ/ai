"""
会话服务 - 统一Flask和FastAPI会话业务逻辑
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from .base_service import BaseService
from models.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse,
    SessionSummary,
    SessionStatus,
    SessionConfig,
    SessionStatistics
)
from models.schemas.chat import AIProvider


class SessionService(BaseService):
    """会话服务 - 统一Flask和FastAPI实现"""
    
    def __init__(self, db=None, redis=None):
        super().__init__(db, redis)
    
    async def create_session(self, user_id: str, session_data: SessionCreate) -> SessionResponse:
        """创建新会话"""
        try:
            session_id = str(uuid.uuid4())
            
            # 创建会话配置
            config = SessionConfig(
                ai_provider=session_data.ai_provider,
                model=session_data.model,
                temperature=session_data.temperature,
                max_tokens=session_data.max_tokens,
                system_prompt=session_data.system_prompt,
                metadata=session_data.metadata
            )
            
            # 生成标题（如果未提供）
            title = session_data.title or f"会话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            session = SessionResponse(
                id=session_id,
                title=title,
                user_id=user_id,
                config=config,
                status=SessionStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                message_count=0,
                last_message_at=None,
                is_active=True
            )
            
            # 缓存会话信息
            await self.set_cache(f"session:{session_id}", session.json())
            
            return session
            
        except Exception as e:
            self.logger.error(f"Create session error: {str(e)}")
            raise Exception(f"创建会话错误: {str(e)}")
    
    async def get_session(self, session_id: str, user_id: str) -> Optional[SessionResponse]:
        """获取会话详情"""
        try:
            # 先从缓存获取
            cached_session = await self.get_cache(f"session:{session_id}")
            if cached_session:
                session_data = SessionResponse.parse_raw(cached_session)
                if session_data.user_id == user_id:
                    return session_data
            
            # 模拟从数据库获取
            # 这里应该实现真实的数据库查询
            return None
            
        except Exception as e:
            self.logger.error(f"Get session error: {str(e)}")
            return None
    
    async def update_session(self, session_id: str, user_id: str, update_data: SessionUpdate) -> Optional[SessionResponse]:
        """更新会话"""
        try:
            session = await self.get_session(session_id, user_id)
            if not session:
                return None
            
            # 更新字段
            if update_data.title is not None:
                session.title = update_data.title
            
            if update_data.config is not None:
                session.config = update_data.config
            
            if update_data.metadata is not None:
                session.config.metadata.update(update_data.metadata)
            
            if update_data.status is not None:
                session.status = update_data.status
            
            session.updated_at = datetime.now()
            
            # 更新缓存
            await self.set_cache(f"session:{session_id}", session.json())
            
            return session
            
        except Exception as e:
            self.logger.error(f"Update session error: {str(e)}")
            raise Exception(f"更新会话错误: {str(e)}")
    
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """删除会话"""
        try:
            session = await self.get_session(session_id, user_id)
            if not session:
                return False
            
            # 软删除 - 更新状态
            session.status = SessionStatus.DELETED
            session.is_active = False
            session.updated_at = datetime.now()
            
            # 更新缓存
            await self.set_cache(f"session:{session_id}", session.json())
            
            return True
            
        except Exception as e:
            self.logger.error(f"Delete session error: {str(e)}")
            return False
    
    async def list_sessions(
        self, 
        user_id: str, 
        page: int = 1, 
        size: int = 20,
        search: Optional[str] = None,
        ai_provider: Optional[AIProvider] = None,
        status: Optional[SessionStatus] = None
    ) -> SessionListResponse:
        """获取用户会话列表"""
        try:
            # 模拟会话列表
            sessions = []
            for i in range(min(size, 10)):  # 模拟最多10个会话
                session_summary = SessionSummary(
                    id=str(uuid.uuid4()),
                    title=f"会话 {i+1}",
                    ai_provider=AIProvider.OPENAI,
                    model="gpt-3.5-turbo",
                    status=SessionStatus.ACTIVE,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    message_count=i * 5,
                    last_message_at=datetime.now(),
                    last_message_preview=f"这是会话 {i+1} 的最后一条消息预览..."
                )
                sessions.append(session_summary)
            
            total = 50  # 模拟总数
            pages = (total + size - 1) // size
            
            return SessionListResponse(
                sessions=sessions,
                total=total,
                page=page,
                size=size,
                pages=pages
            )
            
        except Exception as e:
            self.logger.error(f"List sessions error: {str(e)}")
            raise Exception(f"获取会话列表错误: {str(e)}")
    
    async def get_session_statistics(self, user_id: str) -> SessionStatistics:
        """获取会话统计信息"""
        return SessionStatistics(
            total_sessions=25,
            active_sessions=20,
            total_messages=500,
            total_tokens=25000,
            provider_distribution={
                "openai": 15,
                "qwen": 8,
                "claude": 2
            },
            model_distribution={
                "gpt-3.5-turbo": 12,
                "gpt-4": 3,
                "qwen-turbo": 8,
                "claude-3-haiku": 2
            },
            daily_sessions=[
                {"date": "2024-01-01", "sessions": 3, "messages": 25},
                {"date": "2024-01-02", "sessions": 5, "messages": 40}
            ],
            daily_messages=[
                {"date": "2024-01-01", "messages": 25, "tokens": 1250},
                {"date": "2024-01-02", "messages": 40, "tokens": 2000}
            ]
        )
    
    async def archive_session(self, session_id: str, user_id: str) -> bool:
        """归档会话"""
        try:
            session = await self.get_session(session_id, user_id)
            if not session:
                return False
            
            session.status = SessionStatus.ARCHIVED
            session.updated_at = datetime.now()
            
            # 更新缓存
            await self.set_cache(f"session:{session_id}", session.json())
            
            return True
            
        except Exception as e:
            self.logger.error(f"Archive session error: {str(e)}")
            return False
    
    async def restore_session(self, session_id: str, user_id: str) -> bool:
        """恢复会话"""
        try:
            session = await self.get_session(session_id, user_id)
            if not session:
                return False
            
            session.status = SessionStatus.ACTIVE
            session.is_active = True
            session.updated_at = datetime.now()
            
            # 更新缓存
            await self.set_cache(f"session:{session_id}", session.json())
            
            return True
            
        except Exception as e:
            self.logger.error(f"Restore session error: {str(e)}")
            return False
