"""
Redis连接配置
"""

import aioredis
from typing import Optional
from app.core.config import settings


class RedisClient:
    """Redis客户端管理器"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
    
    async def init_redis(self):
        """初始化Redis连接"""
        self.redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_POOL_SIZE,
            socket_timeout=settings.REDIS_TIMEOUT,
            socket_connect_timeout=settings.REDIS_TIMEOUT,
            retry_on_timeout=True
        )
    
    async def close_redis(self):
        """关闭Redis连接"""
        if self.redis:
            await self.redis.close()
    
    async def get_redis(self) -> aioredis.Redis:
        """获取Redis客户端"""
        if not self.redis:
            await self.init_redis()
        return self.redis


# 全局Redis客户端实例
redis_client = RedisClient()


async def get_redis_client() -> aioredis.Redis:
    """获取Redis客户端"""
    return await redis_client.get_redis()


async def init_redis():
    """初始化Redis"""
    await redis_client.init_redis()


async def close_redis():
    """关闭Redis连接"""
    await redis_client.close_redis()
