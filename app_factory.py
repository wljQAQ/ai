"""
Flask应用工厂模块
"""
import os
import logging
from flask import Flask
from flask_cors import CORS

from config.base import BaseConfig, ConfigManager
from core.extensions import init_extensions
from core.middleware import init_middleware
from api.v1 import init_api_v1


def create_app(config_class=None) -> Flask:
    """创建Flask应用实例"""

    # 创建Flask应用
    app = Flask(__name__)

    # 加载配置
    if config_class is None:
        env = os.getenv('FLASK_ENV', 'development')
        if env == 'production':
            from config.production import ProductionConfig
            config_class = ProductionConfig
        elif env == 'testing':
            from config.testing import TestingConfig
            config_class = TestingConfig
        else:
            from config.development import DevelopmentConfig
            config_class = DevelopmentConfig

    app.config.from_object(config_class)

    # 初始化配置管理器
    config_manager = ConfigManager(config_class)
    app.config_manager = config_manager

    # 验证配置
    validation_result = config_manager.validate()
    if not validation_result['valid']:
        app.logger.error(f"Configuration validation failed: {validation_result['errors']}")
        raise RuntimeError("Invalid configuration")

    if validation_result['warnings']:
        app.logger.warning(f"Configuration warnings: {validation_result['warnings']}")

    # 配置日志
    setup_logging(app)

    # 初始化扩展
    init_extensions(app)

    # 初始化中间件
    init_middleware(app)

    # 启用CORS
    CORS(app, origins=["*"])  # 生产环境应该限制origins

    # 注册API蓝图
    init_api_v1(app)

    # 注册错误处理器
    register_error_handlers(app)

    # 健康检查端点
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'version': '1.0.0'}

    app.logger.info("Application created successfully")
    return app


def setup_logging(app: Flask) -> None:
    """设置日志配置"""
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    log_file = app.config.get('LOG_FILE')

    # 设置日志级别
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 如果指定了日志文件，添加文件处理器
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)


def register_error_handlers(app: Flask) -> None:
    """注册错误处理器"""

    @app.errorhandler(404)
    def not_found(error):
        return {
            'success': False,
            'message': 'Resource not found',
            'error_code': 'NOT_FOUND'
        }, 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {str(error)}")
        return {
            'success': False,
            'message': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }, 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {str(error)}")
        return {
            'success': False,
            'message': 'An unexpected error occurred',
            'error_code': 'UNEXPECTED_ERROR'
        }, 500
