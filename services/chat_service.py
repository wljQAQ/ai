"""
聊天服务 - 统一Flask和FastAPI聊天业务逻辑
"""

import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, List, Optional, Dict, Any

from .base_service import BaseService
from config.settings import settings
from models.schemas.chat import (
    ChatResponse,
    StreamChatResponse,
    ProviderInfo,
    ModelInfo,
    ChatStatistics,
    AIProvider,
    MessageRole,
)
from models.schemas.ai_provider import (
    UnifiedChatRequest,
    UnifiedMessage,
    ProviderType,
    OpenAIConfig,
)
from models.schemas.common import MessageRole as CommonMessageRole
from core.model_providers.base_provider import provider_registry, BaseModelProvider


class ChatService(BaseService):
    """聊天服务 - 统一Flask和FastAPI实现

    使用组合模式管理多个AI提供商，支持：
    - 动态提供商切换
    - 统一的聊天接口
    - 错误处理和重试机制
    - 性能监控
    """

    def __init__(
        self,
        session_service=None,
        redis: Optional[Any] = None,
        db: Optional[Any] = None,
        default_provider: Optional[str] = None,
        provider_configs: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        """初始化聊天服务

        Args:
            session_service: 会话服务实例
            redis: Redis连接
            db: 数据库连接
            default_provider: 默认AI提供商（如果不指定则使用配置文件中的值）
            provider_configs: 提供商配置字典（如果不指定则使用配置文件中的值）
        """
        super().__init__(db, redis)
        self.session_service = session_service

        # 使用配置文件中的默认提供商，如果没有指定的话
        self.default_provider = default_provider or settings.default_ai_provider

        # 初始化提供商实例缓存
        self._providers: Dict[str, BaseModelProvider] = {}

        # 从配置文件获取提供商配置，或使用传入的配置
        self.provider_configs = provider_configs or settings.get_all_provider_configs()

        # 初始化默认提供商
        self._initialize_default_provider()

    def _initialize_default_provider(self) -> None:
        """初始化默认提供商"""
        try:
            if self.default_provider in self.provider_configs:
                self._get_or_create_provider(self.default_provider)
                self.logger.info(f"默认提供商 {self.default_provider} 初始化成功")
            else:
                self.logger.warning(f"默认提供商 {self.default_provider} 配置不存在")
        except Exception as e:
            self.logger.error(f"初始化默认提供商失败: {str(e)}")

    def _get_or_create_provider(self, provider_name: str) -> BaseModelProvider:
        """获取或创建提供商实例

        Args:
            provider_name: 提供商名称

        Returns:
            提供商实例

        Raises:
            ValueError: 当提供商配置不存在或创建失败时
        """
        if provider_name in self._providers:
            return self._providers[provider_name]

        if provider_name not in self.provider_configs:
            raise ValueError(f"提供商 {provider_name} 配置不存在")

        try:
            # 获取提供商类型
            provider_type = ProviderType(provider_name.lower())

            # 获取配置数据并确保包含 provider_type
            config_data = self.provider_configs[provider_name].copy()
            config_data["provider_type"] = provider_type

            # 创建提供商实例
            provider = provider_registry.create_provider(provider_type, config_data)

            # 缓存实例
            self._providers[provider_name] = provider
            self.logger.info(f"提供商 {provider_name} 创建成功")

            return provider

        except Exception as e:
            self.logger.error(f"创建提供商 {provider_name} 失败: {str(e)}")
            raise ValueError(f"创建提供商失败: {str(e)}")

    def _convert_to_unified_request(
        self,
        message: str,
        model: str = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> UnifiedChatRequest:
        """将聊天参数转换为统一请求格式

        Args:
            message: 用户消息
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式响应

        Returns:
            统一请求对象
        """
        # 创建消息列表
        messages = [UnifiedMessage(role=CommonMessageRole.USER, content=message)]

        # 使用默认模型如果未指定
        if not model:
            provider = self._get_or_create_provider(self.default_provider)
            model = provider.get_default_model()

        return UnifiedChatRequest(
            messages=messages,
            model=model,
            temperature=temperature or 0.7,
            max_tokens=max_tokens,
            stream=stream,
        )

    async def send_message(
        self,
        session_id: str,
        user_id: str,
        message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
    ) -> ChatResponse:
        """发送聊天消息

        Args:
            session_id: 会话ID
            user_id: 用户ID
            message: 用户消息
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式响应
            provider_name: 指定的提供商名称
            model: 指定的模型名称

        Returns:
            聊天响应对象
        """
        try:
            # 验证输入
            self.validate_required_fields(
                {"session_id": session_id, "user_id": user_id, "message": message},
                ["session_id", "user_id", "message"],
            )

            # 清理输入
            message = self.sanitize_input(message)

            # 获取提供商实例
            provider_name = provider_name or self.default_provider
            provider = self._get_or_create_provider(provider_name)

            # 创建统一请求
            unified_request = self._convert_to_unified_request(
                message=message,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )

            # 调用AI提供商
            unified_response = await provider.chat(unified_request)

            # 转换为聊天响应格式
            response = ChatResponse(
                id=unified_response.id,
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=unified_response.content,
                model=unified_response.model,
                provider=self._convert_provider_type(unified_response.provider),
                created_at=unified_response.created_at,
                prompt_tokens=unified_response.usage.prompt_tokens,
                completion_tokens=unified_response.usage.completion_tokens,
                total_tokens=unified_response.usage.total_tokens,
                finish_reason=unified_response.finish_reason,
            )

            # 缓存响应
            await self.set_cache(
                f"chat_response:{response.id}", response.model_dump_json()
            )

            self.logger.info(
                f"聊天消息发送成功，提供商: {provider_name}, 模型: {unified_response.model}"
            )
            return response

        except Exception as e:
            self.logger.error(f"Chat service error: {str(e)}")
            raise Exception(f"聊天服务错误: {str(e)}")

    def _convert_provider_type(self, provider_type: ProviderType) -> AIProvider:
        """转换提供商类型

        Args:
            provider_type: 统一提供商类型

        Returns:
            聊天模块的提供商类型
        """
        mapping = {
            ProviderType.OPENAI: AIProvider.OPENAI,
            ProviderType.CLAUDE: AIProvider.CLAUDE,
            ProviderType.QWEN: AIProvider.QWEN,
            ProviderType.GEMINI: AIProvider.GEMINI,
            ProviderType.DIFY: AIProvider.DIFY,
        }
        return mapping.get(provider_type, AIProvider.OPENAI)

    def switch_provider(self, provider_name: str) -> None:
        """切换默认提供商

        Args:
            provider_name: 新的默认提供商名称

        Raises:
            ValueError: 当提供商不存在时
        """
        if provider_name not in self.provider_configs:
            raise ValueError(f"提供商 {provider_name} 配置不存在")

        self.default_provider = provider_name
        self.logger.info(f"默认提供商已切换为: {provider_name}")

    def add_provider_config(self, provider_name: str, config: Dict[str, Any]) -> None:
        """添加提供商配置

        Args:
            provider_name: 提供商名称
            config: 提供商配置
        """
        self.provider_configs[provider_name] = config
        self.logger.info(f"已添加提供商配置: {provider_name}")

    def get_provider_status(self, provider_name: str) -> Dict[str, Any]:
        """获取提供商状态

        Args:
            provider_name: 提供商名称

        Returns:
            提供商状态信息
        """
        if provider_name not in self._providers:
            return {"name": provider_name, "status": "not_initialized", "metrics": None}

        provider = self._providers[provider_name]
        metrics = provider.get_metrics()

        return {
            "name": provider_name,
            "status": "active",
            "metrics": {
                "request_count": metrics.request_count,
                "success_count": metrics.success_count,
                "error_count": metrics.error_count,
                "success_rate": (metrics.success_count / max(metrics.request_count, 1))
                * 100,
                "avg_latency_ms": metrics.avg_latency_ms,
                "total_tokens": metrics.total_tokens,
                "total_cost": metrics.total_cost,
            },
        }

    def list_available_providers(self) -> List[str]:
        """列出所有可用的提供商"""
        return list(self.provider_configs.keys())

    async def send_message_stream(
        self,
        session_id: str,
        user_id: str,
        message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[StreamChatResponse, None]:
        """发送流式聊天消息

        Args:
            session_id: 会话ID
            user_id: 用户ID
            message: 用户消息
            temperature: 温度参数
            max_tokens: 最大token数
            provider_name: 指定的提供商名称
            model: 指定的模型名称

        Yields:
            流式聊天响应对象
        """
        try:
            # 验证输入
            self.validate_required_fields(
                {"session_id": session_id, "user_id": user_id, "message": message},
                ["session_id", "user_id", "message"],
            )

            # 清理输入
            message = self.sanitize_input(message)

            # 获取提供商实例
            provider_name = provider_name or self.default_provider
            provider = self._get_or_create_provider(provider_name)

            # 创建统一请求
            unified_request = self._convert_to_unified_request(
                message=message,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            # 调用AI提供商流式接口
            async for unified_stream_response in provider.chat_stream(unified_request):
                response = StreamChatResponse(
                    id=unified_stream_response.id,
                    session_id=session_id,
                    delta=unified_stream_response.delta,
                    model=unified_stream_response.model,
                    provider=self._convert_provider_type(
                        unified_stream_response.provider
                    ),
                    created_at=unified_stream_response.created_at,
                    finish_reason=unified_stream_response.finish_reason,
                )
                yield response

            self.logger.info(f"流式聊天消息发送成功，提供商: {provider_name}")

        except Exception as e:
            self.logger.error(f"Stream chat service error: {str(e)}")
            raise Exception(f"流式聊天服务错误: {str(e)}")

    async def regenerate_response(
        self, session_id: str, user_id: str, message_id: Optional[str] = None
    ) -> ChatResponse:
        """重新生成回复"""
        try:
            # 模拟重新生成
            response_content = "这是重新生成的AI回复。"

            response = ChatResponse(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=response_content,
                model="gpt-3.5-turbo",
                provider=AIProvider.OPENAI,
                created_at=datetime.now(),
                prompt_tokens=10,
                completion_tokens=len(response_content.split()),
                total_tokens=10 + len(response_content.split()),
                finish_reason="stop",
            )

            return response

        except Exception as e:
            self.logger.error(f"Regenerate response error: {str(e)}")
            raise Exception(f"重新生成回复错误: {str(e)}")

    async def get_available_providers(self) -> List[ProviderInfo]:
        """获取可用的AI提供商"""
        return [
            ProviderInfo(
                name=AIProvider.OPENAI,
                display_name="OpenAI",
                description="OpenAI GPT模型",
                models=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                is_available=True,
                default_model="gpt-3.5-turbo",
            ),
            ProviderInfo(
                name=AIProvider.QWEN,
                display_name="通义千问",
                description="阿里云通义千问模型",
                models=["qwen-turbo", "qwen-plus", "qwen-max"],
                is_available=True,
                default_model="qwen-turbo",
            ),
            ProviderInfo(
                name=AIProvider.CLAUDE,
                display_name="Claude",
                description="Anthropic Claude模型",
                models=["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"],
                is_available=True,
                default_model="claude-3-haiku",
            ),
        ]

    async def get_provider_models(self, provider_name: str) -> List[ModelInfo]:
        """获取指定提供商的模型列表"""
        models_map = {
            "openai": [
                ModelInfo(
                    id="gpt-3.5-turbo",
                    name="GPT-3.5 Turbo",
                    provider=AIProvider.OPENAI,
                    description="快速、经济的GPT模型",
                    max_tokens=4096,
                    input_price=0.0015,
                    output_price=0.002,
                    is_available=True,
                ),
                ModelInfo(
                    id="gpt-4",
                    name="GPT-4",
                    provider=AIProvider.OPENAI,
                    description="最强大的GPT模型",
                    max_tokens=8192,
                    input_price=0.03,
                    output_price=0.06,
                    is_available=True,
                ),
            ],
            "qwen": [
                ModelInfo(
                    id="qwen-turbo",
                    name="通义千问-Turbo",
                    provider=AIProvider.QWEN,
                    description="快速响应的千问模型",
                    max_tokens=6000,
                    input_price=0.008,
                    output_price=0.008,
                    is_available=True,
                )
            ],
            "claude": [
                ModelInfo(
                    id="claude-3-haiku",
                    name="Claude 3 Haiku",
                    provider=AIProvider.CLAUDE,
                    description="快速的Claude模型",
                    max_tokens=4096,
                    input_price=0.00025,
                    output_price=0.00125,
                    is_available=True,
                )
            ],
        }

        return models_map.get(provider_name.lower(), [])

    async def get_chat_statistics(self) -> ChatStatistics:
        """获取聊天统计信息"""
        return ChatStatistics(
            total_messages=1000,
            total_tokens=50000,
            total_cost=25.50,
            provider_stats={
                "openai": {"requests": 800, "tokens": 40000, "cost": 20.00},
                "qwen": {"requests": 200, "tokens": 10000, "cost": 5.50},
            },
            model_stats={
                "gpt-3.5-turbo": {"requests": 600, "tokens": 30000, "cost": 15.00},
                "gpt-4": {"requests": 200, "tokens": 10000, "cost": 5.00},
            },
            daily_stats=[
                {"date": "2024-01-01", "messages": 100, "tokens": 5000, "cost": 2.50},
                {"date": "2024-01-02", "messages": 120, "tokens": 6000, "cost": 3.00},
            ],
        )
