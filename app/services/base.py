"""
基础服务类
"""

from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import aioredis
from loguru import logger

from app.core.config import settings


class BaseService:
    """基础服务类"""
    
    def __init__(self, db: AsyncSession, redis: Optional[aioredis.Redis] = None):
        self.db = db
        self.redis = redis
        self.logger = logger
    
    async def get_cache(self, key: str) -> Optional[str]:
        """从缓存获取数据"""
        if not self.redis:
            return None
        
        try:
            cache_key = f"{settings.CACHE_PREFIX}{key}"
            return await self.redis.get(cache_key)
        except Exception as e:
            self.logger.warning(f"Cache get error: {e}")
            return None
    
    async def set_cache(
        self, 
        key: str, 
        value: str, 
        ttl: int = settings.CACHE_TTL
    ) -> bool:
        """设置缓存数据"""
        if not self.redis:
            return False
        
        try:
            cache_key = f"{settings.CACHE_PREFIX}{key}"
            await self.redis.setex(cache_key, ttl, value)
            return True
        except Exception as e:
            self.logger.warning(f"Cache set error: {e}")
            return False
    
    async def delete_cache(self, key: str) -> bool:
        """删除缓存数据"""
        if not self.redis:
            return False
        
        try:
            cache_key = f"{settings.CACHE_PREFIX}{key}"
            await self.redis.delete(cache_key)
            return True
        except Exception as e:
            self.logger.warning(f"Cache delete error: {e}")
            return False
    
    async def get_cache_pattern(self, pattern: str) -> list:
        """根据模式获取缓存键"""
        if not self.redis:
            return []
        
        try:
            cache_pattern = f"{settings.CACHE_PREFIX}{pattern}"
            return await self.redis.keys(cache_pattern)
        except Exception as e:
            self.logger.warning(f"Cache pattern error: {e}")
            return []
