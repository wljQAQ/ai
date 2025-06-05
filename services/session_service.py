"""
会话服务实现
"""
import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from adapters.base import ChatMessage, MessageRole


@dataclass
class Session:
    """会话数据结构"""
    id: str
    user_id: str
    title: str
    ai_provider: str
    model: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'ai_provider': self.ai_provider,
            'model': self.model,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active,
            'metadata': self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """从字典创建实例"""
        return cls(
            id=data['id'],
            user_id=data['user_id'],
            title=data['title'],
            ai_provider=data['ai_provider'],
            model=data['model'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            is_active=data.get('is_active', True),
            metadata=data.get('metadata')
        )


@dataclass
class SessionConfig:
    """会话配置"""
    ai_provider: str
    model: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'ai_provider': self.ai_provider,
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'system_prompt': self.system_prompt,
            'metadata': self.metadata or {}
        }


class SessionService:
    """会话服务"""
    
    def __init__(self, session_repository, message_repository, cache_service=None):
        self.session_repo = session_repository
        self.message_repo = message_repository
        self.cache = cache_service
        self.logger = logging.getLogger(__name__)
    
    async def create_session(self, user_id: str, config: SessionConfig, title: str = None) -> Session:
        """创建新会话"""
        try:
            # 生成会话ID
            session_id = f"sess_{uuid.uuid4().hex[:12]}"
            
            # 生成默认标题
            if not title:
                title = f"Chat with {config.model}"
            
            # 创建会话对象
            now = datetime.utcnow()
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
            
            # 保存到数据库
            await self.session_repo.create(session.to_dict())
            
            # 如果有系统提示，添加系统消息
            if config.system_prompt:
                system_message = ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=config.system_prompt,
                    timestamp=now
                )
                await self.add_message(session_id, system_message)
            
            # 保存会话配置
            await self._save_session_config(session_id, config)
            
            # 清除用户会话列表缓存
            if self.cache:
                await self.cache.delete(f"user_sessions:{user_id}")
            
            self.logger.info(f"Created session {session_id} for user {user_id}")
            return session
        
        except Exception as e:
            self.logger.error(f"Failed to create session: {str(e)}")
            raise
    
    async def get_session(self, session_id: str, user_id: str) -> Optional[Session]:
        """获取会话"""
        try:
            # 先从缓存获取
            if self.cache:
                cached_data = await self.cache.get(f"session:{session_id}")
                if cached_data:
                    session = Session.from_dict(cached_data)
                    # 验证用户权限
                    if session.user_id == user_id:
                        return session
            
            # 从数据库获取
            session_data = await self.session_repo.get_by_id(session_id)
            if not session_data:
                return None
            
            session = Session.from_dict(session_data)
            
            # 验证用户权限
            if session.user_id != user_id:
                return None
            
            # 缓存会话数据
            if self.cache:
                await self.cache.set(f"session:{session_id}", session.to_dict(), ttl=1800)
            
            return session
        
        except Exception as e:
            self.logger.error(f"Failed to get session {session_id}: {str(e)}")
            raise
    
    async def list_sessions(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Session]:
        """获取用户会话列表"""
        try:
            # 先从缓存获取
            cache_key = f"user_sessions:{user_id}:{limit}:{offset}"
            if self.cache:
                cached_data = await self.cache.get(cache_key)
                if cached_data:
                    return [Session.from_dict(data) for data in cached_data]
            
            # 从数据库获取
            filters = {
                'user_id': user_id,
                'is_active': True
            }
            sessions_data = await self.session_repo.list(
                filters=filters,
                limit=limit,
                offset=offset,
                order_by='updated_at DESC'
            )
            
            sessions = [Session.from_dict(data) for data in sessions_data]
            
            # 缓存结果
            if self.cache:
                await self.cache.set(cache_key, [s.to_dict() for s in sessions], ttl=600)
            
            return sessions
        
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
            
            # 更新时间
            kwargs['updated_at'] = datetime.utcnow()
            
            # 更新数据库
            success = await self.session_repo.update(session_id, kwargs)
            
            if success:
                # 清除相关缓存
                if self.cache:
                    await self.cache.delete(f"session:{session_id}")
                    await self.cache.delete(f"user_sessions:{user_id}")
                
                self.logger.info(f"Updated session {session_id}")
            
            return success
        
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
            success = await self.session_repo.update(session_id, {
                'is_active': False,
                'updated_at': datetime.utcnow()
            })
            
            if success:
                # 清除相关缓存
                if self.cache:
                    await self.cache.delete(f"session:{session_id}")
                    await self.cache.delete(f"user_sessions:{user_id}")
                
                self.logger.info(f"Deleted session {session_id}")
            
            return success
        
        except Exception as e:
            self.logger.error(f"Failed to delete session {session_id}: {str(e)}")
            raise
    
    async def add_message(self, session_id: str, message: ChatMessage) -> bool:
        """添加消息到会话"""
        try:
            # 获取下一个序列号
            sequence_number = await self._get_next_sequence_number(session_id)
            
            # 准备消息数据
            message_data = {
                'id': f"msg_{uuid.uuid4().hex[:12]}",
                'session_id': session_id,
                'role': message.role.value,
                'content': message.content,
                'created_at': message.timestamp or datetime.utcnow(),
                'metadata': message.metadata or {},
                'sequence_number': sequence_number
            }
            
            # 保存消息
            await self.message_repo.create(message_data)
            
            # 更新会话的更新时间
            await self.session_repo.update(session_id, {
                'updated_at': datetime.utcnow()
            })
            
            # 清除消息缓存
            if self.cache:
                await self.cache.delete(f"session_messages:{session_id}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to add message to session {session_id}: {str(e)}")
            raise
    
    async def get_messages(self, session_id: str, limit: int = 50, offset: int = 0) -> List[ChatMessage]:
        """获取会话消息"""
        try:
            # 先从缓存获取
            cache_key = f"session_messages:{session_id}:{limit}:{offset}"
            if self.cache:
                cached_data = await self.cache.get(cache_key)
                if cached_data:
                    return [ChatMessage.from_dict(data) for data in cached_data]
            
            # 从数据库获取
            filters = {'session_id': session_id}
            messages_data = await self.message_repo.list(
                filters=filters,
                limit=limit,
                offset=offset,
                order_by='sequence_number ASC'
            )
            
            messages = []
            for data in messages_data:
                message = ChatMessage(
                    role=MessageRole(data['role']),
                    content=data['content'],
                    timestamp=data['created_at'],
                    metadata=data.get('metadata', {})
                )
                messages.append(message)
            
            # 缓存结果
            if self.cache:
                await self.cache.set(cache_key, [m.to_dict() for m in messages], ttl=600)
            
            return messages
        
        except Exception as e:
            self.logger.error(f"Failed to get messages for session {session_id}: {str(e)}")
            raise
    
    async def _get_next_sequence_number(self, session_id: str) -> int:
        """获取下一个序列号"""
        try:
            # 获取当前最大序列号
            filters = {'session_id': session_id}
            messages = await self.message_repo.list(
                filters=filters,
                limit=1,
                order_by='sequence_number DESC'
            )
            
            if messages:
                return messages[0]['sequence_number'] + 1
            else:
                return 1
        
        except Exception as e:
            self.logger.error(f"Failed to get next sequence number for session {session_id}: {str(e)}")
            return 1
    
    async def _save_session_config(self, session_id: str, config: SessionConfig) -> None:
        """保存会话配置"""
        # 这里可以保存到session_configs表或者session的metadata字段
        # 简化实现，保存到session的metadata中
        pass
