"""
基础配置模块
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """数据库配置"""
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class RedisConfig:
    """Redis配置"""
    url: str
    max_connections: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5


@dataclass
class AIProviderConfig:
    """AI提供商配置"""
    name: str
    api_key: str
    base_url: str
    models: list
    timeout: int = 30
    max_retries: int = 3


class BaseConfig:
    """基础配置类"""
    
    # 应用配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    TESTING = False
    
    # 数据库配置
    DATABASE_URL = os.getenv('DATABASE_URL', 'mysql://root:password@localhost:3306/ai_chat')
    
    # Redis配置
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # API配置
    API_VERSION = 'v1'
    API_PREFIX = f'/api/{API_VERSION}'
    
    # 分页配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # 缓存配置
    CACHE_DEFAULT_TIMEOUT = 300  # 5分钟
    CACHE_KEY_PREFIX = 'ai_chat:'
    
    # 安全配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1小时
    JWT_REFRESH_TOKEN_EXPIRES = 86400 * 7  # 7天
    
    # 限流配置
    RATE_LIMIT_STORAGE_URL = REDIS_URL
    RATE_LIMIT_DEFAULT = "100/hour"
    RATE_LIMIT_CHAT = "60/minute"
    
    # AI提供商配置
    AI_PROVIDERS = {
        'openai': {
            'adapter_class': 'adapters.openai_adapter.OpenAIAdapter',
            'config': {
                'api_key': os.getenv('OPENAI_API_KEY'),
                'base_url': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
                'models': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo'],
                'timeout': 30,
                'max_retries': 3
            }
        },
        'qwen': {
            'adapter_class': 'adapters.qwen_adapter.QwenAdapter',
            'config': {
                'api_key': os.getenv('QWEN_API_KEY'),
                'base_url': os.getenv('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/api/v1'),
                'models': ['qwen-turbo', 'qwen-plus', 'qwen-max'],
                'timeout': 30,
                'max_retries': 3
            }
        },
        'dify': {
            'adapter_class': 'adapters.dify_adapter.DifyAdapter',
            'config': {
                'api_key': os.getenv('DIFY_API_KEY'),
                'base_url': os.getenv('DIFY_BASE_URL'),
                'models': ['dify-chat'],
                'timeout': 30,
                'max_retries': 3
            }
        }
    }
    
    @classmethod
    def get_database_config(cls) -> DatabaseConfig:
        """获取数据库配置"""
        return DatabaseConfig(
            url=cls.DATABASE_URL,
            pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '20')),
            pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', '30')),
            pool_recycle=int(os.getenv('DB_POOL_RECYCLE', '3600'))
        )
    
    @classmethod
    def get_redis_config(cls) -> RedisConfig:
        """获取Redis配置"""
        return RedisConfig(
            url=cls.REDIS_URL,
            max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', '10')),
            socket_timeout=int(os.getenv('REDIS_SOCKET_TIMEOUT', '5')),
            socket_connect_timeout=int(os.getenv('REDIS_CONNECT_TIMEOUT', '5'))
        )
    
    @classmethod
    def get_ai_provider_config(cls, provider_name: str) -> Optional[AIProviderConfig]:
        """获取AI提供商配置"""
        provider_data = cls.AI_PROVIDERS.get(provider_name)
        if not provider_data:
            return None
        
        config = provider_data['config']
        return AIProviderConfig(
            name=provider_name,
            api_key=config['api_key'],
            base_url=config['base_url'],
            models=config['models'],
            timeout=config.get('timeout', 30),
            max_retries=config.get('max_retries', 3)
        )
    
    @classmethod
    def get_available_providers(cls) -> list:
        """获取可用的AI提供商列表"""
        available = []
        for name, config in cls.AI_PROVIDERS.items():
            if config['config'].get('api_key'):
                available.append(name)
        return available
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """验证配置"""
        errors = []
        warnings = []
        
        # 检查必需的环境变量
        required_vars = ['SECRET_KEY', 'DATABASE_URL']
        for var in required_vars:
            if not getattr(cls, var) or getattr(cls, var) == f'dev-{var.lower()}-change-in-production':
                errors.append(f'Missing or default value for {var}')
        
        # 检查AI提供商配置
        available_providers = cls.get_available_providers()
        if not available_providers:
            warnings.append('No AI providers configured')
        
        # 检查数据库连接
        try:
            db_config = cls.get_database_config()
            if not db_config.url:
                errors.append('Invalid database URL')
        except Exception as e:
            errors.append(f'Database configuration error: {str(e)}')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'available_providers': available_providers
        }


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_class=None):
        self.config = config_class or BaseConfig
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return getattr(self.config, key, default)
    
    def get_ai_provider_config(self, provider: str) -> Optional[AIProviderConfig]:
        """获取AI提供商配置"""
        return self.config.get_ai_provider_config(provider)
    
    def get_database_config(self) -> DatabaseConfig:
        """获取数据库配置"""
        return self.config.get_database_config()
    
    def get_redis_config(self) -> RedisConfig:
        """获取Redis配置"""
        return self.config.get_redis_config()
    
    def validate(self) -> Dict[str, Any]:
        """验证配置"""
        return self.config.validate_config()


# 全局配置管理器实例
config_manager = ConfigManager()
