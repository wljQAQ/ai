"""
开发环境配置
"""
from .base import BaseConfig


class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    DEBUG = True
    TESTING = False
