"""
OpenAI模型提供商实现
"""

from typing import Dict, List, AsyncGenerator, Any, Optional
import uuid
from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from .base_provider import BaseModelProvider, provider_registry
from models.schemas.ai_provider import (
    OpenAIConfig,
    UnifiedChatRequest,
    UnifiedChatResponse,
    UnifiedStreamResponse,
    UnifiedMessage,
    TokenUsage,
    ProviderType,
    MessageRole,
)


class OpenAIProvider(BaseModelProvider):
    """OpenAI 模型提供商实现

    实现 OpenAI GPT 系列模型的统一接口，包括：
    - GPT-3.5 Turbo 系列
    - GPT-4 系列
    - GPT-4o 系列
    """

    def __init__(self, config: OpenAIConfig):
        """初始化 OpenAI 提供商

        Args:
            config: OpenAI 配置对象
        """
        self.openai_config = config
        super().__init__(config)

    def _get_provider_type(self) -> ProviderType:
        """获取提供商类型"""
        return ProviderType.OPENAI

    def _validate_config(self) -> None:
        """验证配置"""
        # 配置验证已在 OpenAIConfig 中完成
        if not self.openai_config.api_key:
            raise ValueError("OpenAI API key is required")

    def _initialize_client(self) -> None:
        print(f"self.openai_config.base_url: {self.openai_config.base_url}")

        """初始化 OpenAI 客户端"""
        self.client = AsyncOpenAI(
            api_key=self.openai_config.api_key,
            base_url=self.openai_config.base_url,
            timeout=self.openai_config.timeout,
            max_retries=self.openai_config.max_retries,
        )

    def _convert_to_openai_messages(
        self, messages: List[UnifiedMessage]
    ) -> List[Dict[str, str]]:
        """将统一消息格式转换为 OpenAI 格式

        Args:
            messages: 统一消息列表

        Returns:
            OpenAI 格式的消息列表
        """
        openai_messages = []
        for msg in messages:
            openai_msg = {"role": msg.role.value, "content": msg.content}
            if msg.name:
                openai_msg["name"] = msg.name
            if msg.function_call:
                openai_msg["function_call"] = msg.function_call
            openai_messages.append(openai_msg)
        return openai_messages

    async def _call_api(self, request: UnifiedChatRequest) -> UnifiedChatResponse:
        """调用 OpenAI API

        Args:
            request: 统一聊天请求

        Returns:
            统一聊天响应
        """
        # 转换消息格式
        openai_messages = self._convert_to_openai_messages(request.messages)

        # 构建 OpenAI API 参数
        api_params = {
            "model": request.model,
            "messages": openai_messages,
            "temperature": request.temperature,
            "stream": False,
        }

        # 添加可选参数
        if request.max_tokens:
            api_params["max_tokens"] = request.max_tokens
        if request.top_p:
            api_params["top_p"] = request.top_p
        if request.frequency_penalty:
            api_params["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty:
            api_params["presence_penalty"] = request.presence_penalty
        if request.stop:
            api_params["stop"] = request.stop
        if request.user:
            api_params["user"] = request.user

        # 添加扩展参数
        api_params.update(request.extra_params)

        # 调用 OpenAI API
        response: ChatCompletion = await self.client.chat.completions.create(
            **api_params
        )

        # 构造统一响应
        return UnifiedChatResponse(
            id=response.id,
            content=response.choices[0].message.content or "",
            model=response.model,
            provider=ProviderType.OPENAI,
            usage=TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            ),
            finish_reason=response.choices[0].finish_reason or "stop",
        )

    async def _call_stream_api(
        self, request: UnifiedChatRequest
    ) -> AsyncGenerator[UnifiedStreamResponse, None]:
        """调用 OpenAI 流式 API

        Args:
            request: 统一聊天请求

        Yields:
            统一流式响应
        """
        # 转换消息格式
        openai_messages = self._convert_to_openai_messages(request.messages)

        # 构建 OpenAI API 参数
        api_params = {
            "model": request.model,
            "messages": openai_messages,
            "temperature": request.temperature,
            "stream": True,
        }

        # 添加可选参数
        if request.max_tokens:
            api_params["max_tokens"] = request.max_tokens
        if request.top_p:
            api_params["top_p"] = request.top_p
        if request.frequency_penalty:
            api_params["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty:
            api_params["presence_penalty"] = request.presence_penalty
        if request.stop:
            api_params["stop"] = request.stop
        if request.user:
            api_params["user"] = request.user

        # 添加扩展参数
        api_params.update(request.extra_params)

        # 调用 OpenAI 流式 API
        stream = await self.client.chat.completions.create(**api_params)

        response_id = str(uuid.uuid4())

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield UnifiedStreamResponse(
                    id=response_id,
                    delta=chunk.choices[0].delta.content,
                    model=chunk.model,
                    provider=ProviderType.OPENAI,
                    finish_reason=chunk.choices[0].finish_reason,
                )


# 注册提供商
provider_registry.register(ProviderType.OPENAI, OpenAIProvider, OpenAIConfig)
