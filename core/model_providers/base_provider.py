"""
AI模型提供商基类模块
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncGenerator, Any


class BaseModelProvider(ABC):
    """AI模型提供商基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = self._get_provider_name()
        self.logger = logging.getLogger(f"{__name__}.{self.provider_name}")

        # 验证配置
        self._validate_config()

    @abstractmethod
    def _get_provider_name(self) -> str:
        """获取提供商名称"""
        pass

    @abstractmethod
    def _validate_config(self) -> None:
        """验证配置"""
        pass

    @abstractmethod
    async def chat(self, request) -> Any:
        """同步聊天接口"""
        pass

    @abstractmethod
    async def chat_stream(self, request) -> AsyncGenerator[Any, None]:
        """流式聊天接口"""
        pass

    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        pass

    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)


class ProviderRegistry:
    """模型提供商注册表"""

    def __init__(self):
        self._providers: Dict[str, type] = {}

    def register(self, name: str, provider_class: type) -> None:
        """注册提供商"""
        if not issubclass(provider_class, BaseModelProvider):
            raise ValueError(f"Provider class must inherit from BaseModelProvider")

        self._providers[name] = provider_class

    def get(self, name: str) -> Optional[type]:
        """获取提供商类"""
        return self._providers.get(name)

    def list_providers(self) -> List[str]:
        """列出所有注册的提供商"""
        return list(self._providers.keys())

    def create_provider(self, name: str, config: Dict[str, Any]) -> BaseModelProvider:
        """创建提供商实例"""
        provider_class = self.get(name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {name}")

        return provider_class(config)


# 全局提供商注册表
provider_registry = ProviderRegistry()