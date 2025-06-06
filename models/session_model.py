"""
会话相关数据模型
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class SessionConfig:
    """会话配置模型"""
    ai_provider: str
    model: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
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
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionConfig':
        """从字典创建实例"""
        return cls(
            ai_provider=data['ai_provider'],
            model=data['model'],
            temperature=data.get('temperature', 0.7),
            max_tokens=data.get('max_tokens'),
            system_prompt=data.get('system_prompt'),
            metadata=data.get('metadata', {})
        )


@dataclass
class Session:
    """会话模型"""
    id: str
    user_id: str
    title: str
    ai_provider: str
    model: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
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
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at'],
            updated_at=datetime.fromisoformat(data['updated_at']) if isinstance(data['updated_at'], str) else data['updated_at'],
            is_active=data.get('is_active', True),
            metadata=data.get('metadata', {})
        )
