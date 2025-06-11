"""
应用配置管理 - 统一管理环境变量和配置
"""

import os
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class DatabaseSettings(BaseSettings):
    """数据库配置"""

    # 支持完整的数据库URL
    url: str = Field(default="mysql://root:password@localhost:3306/ai_chat", description="数据库连接URL")

    # 连接池配置
    pool_size: int = Field(default=10, description="连接池大小")
    max_overflow: int = Field(default=20, description="连接池最大溢出")
    pool_timeout: int = Field(default=30, description="连接池超时时间")
    pool_recycle: int = Field(default=3600, description="连接池回收时间")

    class Config:
        env_prefix = "DB_"
        env_file = ".env"
        extra = "ignore"  # 忽略额外字段


class RedisSettings(BaseSettings):
    """Redis配置"""

    # 支持完整的Redis URL
    url: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")

    # 连接配置
    max_connections: int = Field(default=10, description="最大连接数")
    socket_timeout: int = Field(default=5, description="Socket超时时间")
    connect_timeout: int = Field(default=5, description="连接超时时间")

    class Config:
        env_prefix = "REDIS_"
        env_file = ".env"
        extra = "ignore"  # 忽略额外字段


class LogSettings(BaseSettings):
    """日志配置"""

    level: str = Field(default="INFO", description="日志级别")
    file: str = Field(default="logs/app.log", description="日志文件路径")

    class Config:
        env_prefix = "LOG_"
        env_file = ".env"
        extra = "ignore"


class JWTSettings(BaseSettings):
    """JWT配置"""

    secret_key: str = Field(default="your-jwt-secret-key", description="JWT密钥")
    access_token_expires: int = Field(default=3600, description="访问令牌过期时间(秒)")
    refresh_token_expires: int = Field(default=604800, description="刷新令牌过期时间(秒)")

    class Config:
        env_prefix = "JWT_"
        env_file = ".env"
        extra = "ignore"


class RateLimitSettings(BaseSettings):
    """限流配置"""

    storage_url: str = Field(default="redis://localhost:6379/1", description="限流存储URL")
    default: str = Field(default="100/hour", description="默认限流规则")
    chat: str = Field(default="60/minute", description="聊天限流规则")

    class Config:
        env_prefix = "RATE_LIMIT_"
        env_file = ".env"
        extra = "ignore"


class OpenAISettings(BaseSettings):
    """OpenAI配置"""

    api_key: str = Field(description="OpenAI API密钥")
    base_url: Optional[str] = Field(default=None, description="OpenAI API基础URL")
    default_model: str = Field(default="qwen-plus", description="默认模型")
    timeout: float = Field(default=30.0, description="请求超时时间")
    max_retries: int = Field(default=3, description="最大重试次数")

    class Config:
        env_prefix = "OPENAI_"
        env_file = ".env"
        extra = "ignore"


class QwenSettings(BaseSettings):
    """通义千问配置"""

    api_key: str = Field(description="通义千问API密钥")
    base_url: Optional[str] = Field(default=None, description="通义千问API基础URL")
    default_model: str = Field(default="qwen3-32b", description="默认模型")
    timeout: float = Field(default=30.0, description="请求超时时间")
    max_retries: int = Field(default=3, description="最大重试次数")

    class Config:
        env_prefix = "QWEN_"
        env_file = ".env"
        extra = "ignore"


class DifySettings(BaseSettings):
    """Dify配置"""

    api_key: str = Field(description="Dify API密钥")
    base_url: str = Field(default="https://api.dify.ai/v1", description="Dify API基础URL")

    class Config:
        env_prefix = "DIFY_"
        env_file = ".env"
        extra = "ignore"


class AppSettings(BaseSettings):
    """应用主配置"""

    # 应用基础配置
    debug: bool = Field(default=False, description="调试模式")
    secret_key: str = Field(default="your-secret-key-change-in-production", description="应用密钥")
    default_ai_provider: str = Field(default="openai", description="默认AI提供商")

    # 分页配置
    default_page_size: int = Field(default=20, description="默认分页大小")
    max_page_size: int = Field(default=100, description="最大分页大小")

    # 缓存配置
    cache_default_timeout: int = Field(default=300, description="默认缓存超时时间")

    # 子配置
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    log: LogSettings = Field(default_factory=LogSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    qwen: QwenSettings = Field(default_factory=QwenSettings)
    dify: DifySettings = Field(default_factory=DifySettings)

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 忽略额外字段

    def get_all_provider_configs(self) -> Dict[str, Any]:
        """获取所有AI提供商配置"""
        return {
            'openai': {
                'api_key': self.openai.api_key,
                'base_url': self.openai.base_url,
                'default_model': self.openai.default_model,
                'timeout': self.openai.timeout,
                'max_retries': self.openai.max_retries,
            },
            'qwen': {
                'api_key': self.qwen.api_key,
                'base_url': self.qwen.base_url,
                'default_model': self.qwen.default_model,
                'timeout': self.qwen.timeout,
                'max_retries': self.qwen.max_retries,
            },
            'dify': {
                'api_key': self.dify.api_key,
                'base_url': self.dify.base_url,
            }
        }


# 全局配置实例
settings = AppSettings()
