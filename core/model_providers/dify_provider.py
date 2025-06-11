"""
Dify模型提供商实现
适配 Dify AI 平台的 Chat API
"""

from typing import Dict, List, AsyncGenerator, Any, Optional
import uuid
import json
import httpx

from .base_provider import BaseModelProvider, provider_registry
from models.schemas.ai_provider import (
    DifyConfig,
    UnifiedChatRequest,
    UnifiedChatResponse,
    UnifiedStreamResponse,
    UnifiedMessage,
    TokenUsage,
    ProviderType,
    MessageRole,
)


class DifyProvider(BaseModelProvider):
    """Dify 模型提供商实现

    实现 Dify AI 平台的统一接口，包括：
    - 对话补全接口 (chat completions)
    - 流式响应支持
    - 错误处理和重试机制
    - 对话状态管理
    """

    def __init__(self, config: DifyConfig):
        """初始化 Dify 提供商

        Args:
            config: Dify 配置对象
        """
        self.dify_config = config
        super().__init__(config)

    def _get_provider_type(self) -> ProviderType:
        """获取提供商类型"""
        return ProviderType.DIFY

    def _validate_config(self) -> None:
        """验证配置"""
        if not self.dify_config.api_key:
            raise ValueError("Dify API key is required")
        if not self.dify_config.base_url:
            raise ValueError("Dify base URL is required")

    def _initialize_client(self) -> None:
        """初始化 Dify 客户端"""
        self.client = httpx.AsyncClient(
            base_url=self.dify_config.base_url,
            headers={
                "Authorization": f"Bearer {self.dify_config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.dify_config.timeout,
        )

    def _convert_messages_to_query(self, messages: List[UnifiedMessage]) -> str:
        """将统一消息格式转换为 Dify 查询格式

        Dify API 使用单个 query 字段而不是消息数组
        我们将最后一条用户消息作为查询，其他消息作为上下文

        Args:
            messages: 统一消息列表

        Returns:
            Dify 格式的查询字符串
        """
        if not messages:
            return ""

        # 获取最后一条用户消息作为主要查询
        user_messages = [msg for msg in messages if msg.role == MessageRole.USER]
        if user_messages:
            return user_messages[-1].content

        # 如果没有用户消息，返回最后一条消息的内容
        return messages[-1].content

    def _extract_conversation_context(self, messages: List[UnifiedMessage]) -> Dict[str, Any]:
        """提取对话上下文信息

        Args:
            messages: 统一消息列表

        Returns:
            包含上下文信息的字典
        """
        context = {}
        
        # 提取系统消息作为指令
        system_messages = [msg for msg in messages if msg.role == MessageRole.SYSTEM]
        if system_messages:
            context["system_instruction"] = system_messages[0].content

        # 提取对话历史（除了最后一条用户消息）
        conversation_history = []
        for i, msg in enumerate(messages[:-1]):  # 排除最后一条消息
            if msg.role in [MessageRole.USER, MessageRole.ASSISTANT]:
                conversation_history.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        
        if conversation_history:
            context["conversation_history"] = conversation_history

        return context

    async def _call_api(self, request: UnifiedChatRequest) -> UnifiedChatResponse:
        """调用 Dify API

        Args:
            request: 统一聊天请求

        Returns:
            统一聊天响应
        """
        # 转换消息格式
        query = self._convert_messages_to_query(request.messages)
        context = self._extract_conversation_context(request.messages)

        # 构建 Dify API 参数
        api_params = {
            "inputs": context.get("system_instruction", {}),
            "query": query,
            "response_mode": "blocking",
            "user": request.user or str(uuid.uuid4()),
        }

        # 添加对话ID（如果存在）
        if self.dify_config.conversation_id:
            api_params["conversation_id"] = self.dify_config.conversation_id

        # 添加扩展参数
        api_params.update(request.extra_params)

        # 调用 Dify API
        response = await self.client.post("/v1/chat-messages", json=api_params)
        response.raise_for_status()

        data = response.json()

        # 构造统一响应
        return UnifiedChatResponse(
            id=data.get("id", str(uuid.uuid4())),
            content=data.get("answer", ""),
            model=request.model,  # Dify 不返回具体模型信息，使用请求中的模型
            provider=ProviderType.DIFY,
            usage=TokenUsage(
                prompt_tokens=data.get("metadata", {}).get("usage", {}).get("prompt_tokens", 0),
                completion_tokens=data.get("metadata", {}).get("usage", {}).get("completion_tokens", 0),
                total_tokens=data.get("metadata", {}).get("usage", {}).get("total_tokens", 0),
            ),
            finish_reason="stop",  # Dify 通常不提供详细的结束原因
            extra_data={
                "conversation_id": data.get("conversation_id"),
                "message_id": data.get("message_id"),
                "metadata": data.get("metadata", {}),
            },
        )

    async def _call_stream_api(
        self, request: UnifiedChatRequest
    ) -> AsyncGenerator[UnifiedStreamResponse, None]:
        """调用 Dify 流式 API

        Args:
            request: 统一聊天请求

        Yields:
            统一流式响应
        """
        # 转换消息格式
        query = self._convert_messages_to_query(request.messages)
        context = self._extract_conversation_context(request.messages)

        # 构建 Dify API 参数
        api_params = {
            "inputs": context.get("system_instruction", {}),
            "query": query,
            "response_mode": "streaming",
            "user": request.user or str(uuid.uuid4()),
        }

        # 添加对话ID（如果存在）
        if self.dify_config.conversation_id:
            api_params["conversation_id"] = self.dify_config.conversation_id

        # 添加扩展参数
        api_params.update(request.extra_params)

        response_id = str(uuid.uuid4())

        # 调用 Dify 流式 API
        async with self.client.stream("POST", "/v1/chat-messages", json=api_params) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data_str = line[6:]  # 去掉 "data: " 前缀
                        if data_str.strip() == "[DONE]":
                            break

                        data = json.loads(data_str)
                        event_type = data.get("event")

                        if event_type == "message":
                            # 完整消息事件
                            yield UnifiedStreamResponse(
                                id=response_id,
                                delta=data.get("answer", ""),
                                model=request.model,
                                provider=ProviderType.DIFY,
                                finish_reason="stop",
                            )
                        elif event_type == "message_delta":
                            # 增量消息事件
                            yield UnifiedStreamResponse(
                                id=response_id,
                                delta=data.get("delta", ""),
                                model=request.model,
                                provider=ProviderType.DIFY,
                                finish_reason=None,
                            )
                        elif event_type == "message_end":
                            # 消息结束事件
                            yield UnifiedStreamResponse(
                                id=response_id,
                                delta="",
                                model=request.model,
                                provider=ProviderType.DIFY,
                                finish_reason="stop",
                            )

                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Failed to parse stream data: {e}")
                        continue
                    except Exception as e:
                        self.logger.error(f"Error processing stream data: {e}")
                        continue

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if hasattr(self, "client"):
            await self.client.aclose()


# 注册提供商
provider_registry.register(ProviderType.DIFY, DifyProvider, DifyConfig)
