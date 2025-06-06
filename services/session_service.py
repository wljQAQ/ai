"""
会话服务实现 - 业务逻辑层
"""
import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from models.chat_model import ChatMessage, MessageRole
from models.session_model import Session, SessionConfig


class SessionService:
    """会话服务 - 处理会话相关的业务逻辑"""
    
    def __init__(self, cache_service=None):
        self.cache = cache_service
        self.logger = logging.getLogger(__name__)
        # 简化实现：使用内存存储，实际项目中应该使用数据库
        self._sessions: Dict[str, Session] = {}
        self._messages: Dict[str, List[ChatMessage]] = {}
    
    async def create_session(self, user_id: str, config: SessionConfig, title: str = None) -> Session:
        """创建新会话"""
        try:
            # 生成会话ID
            session_id = f"sess_{uuid.uuid4().hex[:12]}"
            
            # 生成默认标题
            if not title:
                title = f"Chat with {config.model}"
            
            # 创建会话对象
            now = datetime.now()
            session = Session(
                id=session_id,
                user_id=user_id,
                title=title,
                ai_provider=config.ai_provider,
                model=config.model,
                created_at=now,
                updated_at=now,
                is_active=True,
                metadata=config.metadata
            )
            
            # 保存到内存（实际项目中应该保存到数据库）
            self._sessions[session_id] = session
            self._messages[session_id] = []
            
            # 如果有系统提示，添加系统消息
            if config.system_prompt:
                system_message = ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=config.system_prompt,
                    timestamp=now
                )
                await self.add_message(session_id, system_message)
            
            self.logger.info(f"Created session {session_id} for user {user_id}")
            return session
        
        except Exception as e:
            self.logger.error(f"Failed to create session: {str(e)}")
            raise
    
    async def get_session(self, session_id: str, user_id: str) -> Optional[Session]:
        """获取会话"""
        try:
            session = self._sessions.get(session_id)
            if not session:
                return None
            
            # 验证用户权限
            if session.user_id != user_id:
                return None
            
            return session
        
        except Exception as e:
            self.logger.error(f"Failed to get session {session_id}: {str(e)}")
            raise
    
    async def list_sessions(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Session]:
        """获取用户会话列表"""
        try:
            # 过滤用户的会话
            user_sessions = [
                session for session in self._sessions.values()
                if session.user_id == user_id and session.is_active
            ]
            
            # 按更新时间排序
            user_sessions.sort(key=lambda x: x.updated_at, reverse=True)
            
            # 分页
            return user_sessions[offset:offset + limit]
        
        except Exception as e:
            self.logger.error(f"Failed to list sessions for user {user_id}: {str(e)}")
            raise
    
    async def update_session(self, session_id: str, user_id: str, **kwargs) -> bool:
        """更新会话"""
        try:
            # 验证会话存在且属于用户
            session = await self.get_session(session_id, user_id)
            if not session:
                return False
            
            # 更新字段
            if 'title' in kwargs:
                session.title = kwargs['title']
            if 'metadata' in kwargs:
                session.metadata = kwargs['metadata']
            
            # 更新时间
            session.updated_at = datetime.now()
            
            self.logger.info(f"Updated session {session_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to update session {session_id}: {str(e)}")
            raise
    
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """删除会话（软删除）"""
        try:
            # 验证会话存在且属于用户
            session = await self.get_session(session_id, user_id)
            if not session:
                return False
            
            # 软删除
            session.is_active = False
            session.updated_at = datetime.now()
            
            self.logger.info(f"Deleted session {session_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to delete session {session_id}: {str(e)}")
            raise
    
    async def add_message(self, session_id: str, message: ChatMessage) -> bool:
        """添加消息到会话"""
        try:
            # 确保会话存在
            if session_id not in self._sessions:
                raise ValueError(f"Session {session_id} not found")
            
            # 添加消息
            if session_id not in self._messages:
                self._messages[session_id] = []
            
            self._messages[session_id].append(message)
            
            # 更新会话的更新时间
            session = self._sessions[session_id]
            session.updated_at = datetime.now()
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to add message to session {session_id}: {str(e)}")
            raise
    
    async def get_messages(self, session_id: str, limit: int = 50, offset: int = 0) -> List[ChatMessage]:
        """获取会话消息"""
        try:
            messages = self._messages.get(session_id, [])
            
            # 分页
            return messages[offset:offset + limit]
        
        except Exception as e:
            self.logger.error(f"Failed to get messages for session {session_id}: {str(e)}")
            raise
