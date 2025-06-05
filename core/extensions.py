"""
Flask扩展初始化模块
"""
import redis
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from config.base import ConfigManager


# 全局扩展实例
db_engine = None
db_session_factory = None
redis_client = None


def init_extensions(app: Flask) -> None:
    """初始化所有扩展"""
    init_database(app)
    init_redis(app)
    init_ai_adapters(app)


def init_database(app: Flask) -> None:
    """初始化数据库连接"""
    global db_engine, db_session_factory
    
    try:
        config_manager = app.config_manager
        db_config = config_manager.get_database_config()
        
        # 创建数据库引擎
        db_engine = create_engine(
            db_config.url,
            poolclass=QueuePool,
            pool_size=db_config.pool_size,
            max_overflow=db_config.max_overflow,
            pool_timeout=db_config.pool_timeout,
            pool_recycle=db_config.pool_recycle,
            echo=app.config.get('DEBUG', False)
        )
        
        # 创建会话工厂
        db_session_factory = sessionmaker(bind=db_engine)
        
        # 将数据库相关对象添加到应用上下文
        app.db_engine = db_engine
        app.db_session_factory = db_session_factory
        
        app.logger.info("Database initialized successfully")
        
    except Exception as e:
        app.logger.error(f"Failed to initialize database: {str(e)}")
        raise


def init_redis(app: Flask) -> None:
    """初始化Redis连接"""
    global redis_client
    
    try:
        config_manager = app.config_manager
        redis_config = config_manager.get_redis_config()
        
        # 创建Redis客户端
        redis_client = redis.from_url(
            redis_config.url,
            max_connections=redis_config.max_connections,
            socket_timeout=redis_config.socket_timeout,
            socket_connect_timeout=redis_config.socket_connect_timeout,
            decode_responses=True
        )
        
        # 测试连接
        redis_client.ping()
        
        # 将Redis客户端添加到应用上下文
        app.redis_client = redis_client
        
        app.logger.info("Redis initialized successfully")
        
    except Exception as e:
        app.logger.error(f"Failed to initialize Redis: {str(e)}")
        # Redis不是必需的，可以继续运行
        app.redis_client = None


def init_ai_adapters(app: Flask) -> None:
    """初始化AI适配器"""
    try:
        from adapters.factory import AdapterFactory
        from adapters.openai_adapter import OpenAIAdapter
        from adapters.qwen_adapter import QwenAdapter
        from adapters.dify_adapter import DifyAdapter
        
        # 注册适配器
        adapter_factory = AdapterFactory()
        adapter_factory.register('openai', OpenAIAdapter)
        adapter_factory.register('qwen', QwenAdapter)
        adapter_factory.register('dify', DifyAdapter)
        
        # 将适配器工厂添加到应用上下文
        app.adapter_factory = adapter_factory
        
        # 验证可用的适配器
        config_manager = app.config_manager
        available_providers = config_manager.get('AI_PROVIDERS', {})
        
        valid_adapters = []
        for provider_name, provider_config in available_providers.items():
            try:
                adapter = adapter_factory.create_adapter(provider_name, provider_config['config'])
                valid_adapters.append(provider_name)
                app.logger.info(f"AI adapter '{provider_name}' initialized successfully")
            except Exception as e:
                app.logger.warning(f"Failed to initialize AI adapter '{provider_name}': {str(e)}")
        
        app.valid_ai_adapters = valid_adapters
        
        if not valid_adapters:
            app.logger.warning("No valid AI adapters found")
        
    except Exception as e:
        app.logger.error(f"Failed to initialize AI adapters: {str(e)}")
        app.adapter_factory = None
        app.valid_ai_adapters = []


def get_db_session():
    """获取数据库会话"""
    if db_session_factory is None:
        raise RuntimeError("Database not initialized")
    return db_session_factory()


def get_redis_client():
    """获取Redis客户端"""
    return redis_client


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """初始化应用"""
        self.app = app
        app.teardown_appcontext(self.close_db)
    
    def get_session(self):
        """获取数据库会话"""
        return get_db_session()
    
    def close_db(self, error):
        """关闭数据库连接"""
        # 在请求结束时自动关闭会话
        pass


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.redis_client = None
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """初始化应用"""
        self.app = app
        self.redis_client = getattr(app, 'redis_client', None)
    
    async def get(self, key: str):
        """获取缓存值"""
        if not self.redis_client:
            return None
        
        try:
            return self.redis_client.get(key)
        except Exception as e:
            self.app.logger.error(f"Cache get error: {str(e)}")
            return None
    
    async def set(self, key: str, value, ttl: int = None):
        """设置缓存值"""
        if not self.redis_client:
            return False
        
        try:
            if ttl:
                return self.redis_client.setex(key, ttl, value)
            else:
                return self.redis_client.set(key, value)
        except Exception as e:
            self.app.logger.error(f"Cache set error: {str(e)}")
            return False
    
    async def delete(self, key: str):
        """删除缓存值"""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.delete(key)
        except Exception as e:
            self.app.logger.error(f"Cache delete error: {str(e)}")
            return False
    
    async def exists(self, key: str):
        """检查缓存是否存在"""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.exists(key)
        except Exception as e:
            self.app.logger.error(f"Cache exists error: {str(e)}")
            return False


# 全局管理器实例
db_manager = DatabaseManager()
cache_manager = CacheManager()
