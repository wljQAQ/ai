"""
基础服务类 - 统一Flask和FastAPI服务基类
"""

from typing import Any, Dict, Optional
from loguru import logger


class BaseService:
    """基础服务类 - 支持Flask和FastAPI双模式"""

    def __init__(self, db: Optional[Any] = None, redis: Optional[Any] = None):
        self.db = db
        self.redis = redis
        self.logger = logger
        # 缓存配置
        self.cache_prefix = "ai_chat:"
        self.cache_ttl = 300  # 5分钟
    
    async def get_cache(self, key: str) -> Optional[str]:
        """从缓存获取数据"""
        if not self.redis:
            return None
        
        try:
            cache_key = f"{self.cache_prefix}{key}"
            return await self.redis.get(cache_key)
        except Exception as e:
            self.logger.warning(f"Cache get error: {e}")
            return None
    
    async def set_cache(
        self, 
        key: str, 
        value: str, 
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存数据"""
        if not self.redis:
            return False
        
        try:
            cache_key = f"{self.cache_prefix}{key}"
            ttl = ttl or self.cache_ttl
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
            cache_key = f"{self.cache_prefix}{key}"
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
            cache_pattern = f"{self.cache_prefix}{pattern}"
            return await self.redis.keys(cache_pattern)
        except Exception as e:
            self.logger.warning(f"Cache pattern error: {e}")
            return []
    
    def validate_required_fields(self, data: dict, required_fields: list) -> None:
        """验证必需字段"""
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    def sanitize_input(self, text: str, max_length: int = 10000) -> str:
        """清理输入文本"""
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = text.strip()
        
        # 限制长度
        if len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    def create_response_dict(self, data: Any = None, message: str = "Success", success: bool = True) -> dict:
        """创建标准响应字典"""
        return {
            "success": success,
            "message": message,
            "data": data,
            "timestamp": self._get_current_timestamp()
        }
    
    def create_error_response_dict(self, message: str, error_code: str = None, details: dict = None) -> dict:
        """创建错误响应字典"""
        response = {
            "success": False,
            "message": message,
            "timestamp": self._get_current_timestamp()
        }
        
        if error_code:
            response["error_code"] = error_code
        
        if details:
            response["details"] = details
        
        return response
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
