"""
AI模型提供商基类模块
"""
import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncGenerator, Any, Type
from datetime import datetime

from models.schemas.ai_provider import (
    BaseProviderConfig,
    UnifiedChatRequest,
    UnifiedChatResponse,
    UnifiedStreamResponse,
    ProviderError,
    ProviderMetrics,
    ProviderType
)


class BaseModelProvider(ABC):
    """AI模型提供商抽象基类

    定义所有 AI 提供商必须实现的统一接口，包括：
    - 配置管理和验证
    - 统一的聊天接口
    - 错误处理和重试机制
    - 性能监控和指标收集
    """

    def __init__(self, config: BaseProviderConfig):
        """初始化提供商

        Args:
            config: 提供商配置对象
        """
        self.config = config
        self.provider_type = self._get_provider_type()
        self.logger = logging.getLogger(f"{__name__}.{self.provider_type.value}")

        # 性能指标
        self.metrics = ProviderMetrics(
            provider=self.provider_type,
            model=config.default_model
        )

        # 验证配置
        self._validate_config()

        # 初始化客户端
        self._initialize_client()

    @abstractmethod
    def _get_provider_type(self) -> ProviderType:
        """获取提供商类型"""
        pass

    @abstractmethod
    def _validate_config(self) -> None:
        """验证配置

        子类应该实现具体的配置验证逻辑
        """
        pass

    @abstractmethod
    def _initialize_client(self) -> None:
        """初始化客户端

        子类应该在此方法中初始化具体的 API 客户端
        """
        pass

    @abstractmethod
    async def _call_api(self, request: UnifiedChatRequest) -> UnifiedChatResponse:
        """调用具体的 API

        子类必须实现此方法来调用具体提供商的 API

        Args:
            request: 统一的聊天请求

        Returns:
            统一的聊天响应
        """
        pass

    @abstractmethod
    async def _call_stream_api(self, request: UnifiedChatRequest) -> AsyncGenerator[UnifiedStreamResponse, None]:
        """调用流式 API

        子类必须实现此方法来调用具体提供商的流式 API

        Args:
            request: 统一的聊天请求

        Yields:
            统一的流式响应
        """
        pass

    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return self.config.supported_models.copy()

    def get_default_model(self) -> str:
        """获取默认模型"""
        return self.config.default_model

    async def chat(self, request: UnifiedChatRequest) -> UnifiedChatResponse:
        """统一聊天接口

        提供错误处理、重试机制和性能监控

        Args:
            request: 统一的聊天请求

        Returns:
            统一的聊天响应

        Raises:
            ProviderError: 当所有重试都失败时
        """
        start_time = time.time()
        last_error = None

        # 更新请求指标
        self.metrics.request_count += 1

        for attempt in range(self.config.max_retries + 1):
            try:
                self.logger.debug(f"Attempt {attempt + 1} for chat request")

                # 调用具体的 API
                response = await self._call_api(request)

                # 计算延迟
                latency_ms = int((time.time() - start_time) * 1000)
                response.latency_ms = latency_ms

                # 更新成功指标
                self.metrics.success_count += 1
                self.metrics.avg_latency_ms = (
                    (self.metrics.avg_latency_ms * (self.metrics.success_count - 1) + latency_ms)
                    / self.metrics.success_count
                )
                self.metrics.total_tokens += response.usage.total_tokens
                self.metrics.last_updated = datetime.now()

                self.logger.info(f"Chat request successful, latency: {latency_ms}ms")
                return response

            except Exception as e:
                last_error = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")

                # 更新错误指标
                self.metrics.error_count += 1

                # 如果不是最后一次尝试，等待后重试
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                else:
                    break

        # 所有重试都失败了
        self.logger.error(f"All {self.config.max_retries + 1} attempts failed")
        raise ProviderError(
            error_code="MAX_RETRIES_EXCEEDED",
            error_message=f"Failed after {self.config.max_retries + 1} attempts: {str(last_error)}",
            provider=self.provider_type,
            is_retryable=False
        )

    async def chat_stream(self, request: UnifiedChatRequest) -> AsyncGenerator[UnifiedStreamResponse, None]:
        """统一流式聊天接口

        提供错误处理和性能监控

        Args:
            request: 统一的聊天请求

        Yields:
            统一的流式响应

        Raises:
            ProviderError: 当流式调用失败时
        """
        start_time = time.time()

        # 更新请求指标
        self.metrics.request_count += 1

        try:
            self.logger.debug("Starting stream chat request")

            # 调用具体的流式 API
            async for response in self._call_stream_api(request):
                yield response

            # 计算延迟
            latency_ms = int((time.time() - start_time) * 1000)

            # 更新成功指标
            self.metrics.success_count += 1
            self.metrics.avg_latency_ms = (
                (self.metrics.avg_latency_ms * (self.metrics.success_count - 1) + latency_ms)
                / self.metrics.success_count
            )
            self.metrics.last_updated = datetime.now()

            self.logger.info(f"Stream chat request successful, latency: {latency_ms}ms")

        except Exception as e:
            # 更新错误指标
            self.metrics.error_count += 1

            self.logger.error(f"Stream chat request failed: {str(e)}")
            raise ProviderError(
                error_code="STREAM_ERROR",
                error_message=f"Stream chat failed: {str(e)}",
                provider=self.provider_type,
                is_retryable=True
            )

    def get_metrics(self) -> ProviderMetrics:
        """获取性能指标"""
        return self.metrics.model_copy()

    def reset_metrics(self) -> None:
        """重置性能指标"""
        self.metrics = ProviderMetrics(
            provider=self.provider_type,
            model=self.config.default_model
        )


class ProviderRegistry:
    """模型提供商注册表

    管理所有已注册的 AI 提供商，支持：
    - 提供商注册和发现
    - 动态创建提供商实例
    - 配置验证和类型检查
    """

    def __init__(self):
        self._providers: Dict[ProviderType, Type[BaseModelProvider]] = {}
        self._config_classes: Dict[ProviderType, Type[BaseProviderConfig]] = {}

    def register(
        self,
        provider_type: ProviderType,
        provider_class: Type[BaseModelProvider],
        config_class: Type[BaseProviderConfig]
    ) -> None:
        """注册提供商

        Args:
            provider_type: 提供商类型
            provider_class: 提供商实现类
            config_class: 配置类
        """
        if not issubclass(provider_class, BaseModelProvider):
            raise ValueError(f"Provider class must inherit from BaseModelProvider")

        if not issubclass(config_class, BaseProviderConfig):
            raise ValueError(f"Config class must inherit from BaseProviderConfig")

        self._providers[provider_type] = provider_class
        self._config_classes[provider_type] = config_class

    def get_provider_class(self, provider_type: ProviderType) -> Optional[Type[BaseModelProvider]]:
        """获取提供商类"""
        return self._providers.get(provider_type)

    def get_config_class(self, provider_type: ProviderType) -> Optional[Type[BaseProviderConfig]]:
        """获取配置类"""
        return self._config_classes.get(provider_type)

    def list_providers(self) -> List[ProviderType]:
        """列出所有注册的提供商"""
        return list(self._providers.keys())

    def create_provider(self, provider_type: ProviderType, config_data: Dict[str, Any]) -> BaseModelProvider:
        """创建提供商实例

        Args:
            provider_type: 提供商类型
            config_data: 配置数据

        Returns:
            提供商实例

        Raises:
            ValueError: 当提供商未注册或配置无效时
        """
        provider_class = self.get_provider_class(provider_type)
        config_class = self.get_config_class(provider_type)

        if not provider_class or not config_class:
            raise ValueError(f"Unknown provider: {provider_type}")

        # 验证并创建配置对象
        config = config_class(**config_data)

        # 创建提供商实例
        return provider_class(config)

    def is_registered(self, provider_type: ProviderType) -> bool:
        """检查提供商是否已注册"""
        return provider_type in self._providers


# 全局提供商注册表
provider_registry = ProviderRegistry()