"""
Claude模型提供商实现
演示如何轻松添加新的 AI 提供商
"""
from typing import Dict, List, AsyncGenerator, Any, Optional
import uuid
import httpx

from .base_provider import BaseModelProvider, provider_registry
from models.schemas.ai_provider import (
    ClaudeConfig,
    UnifiedChatRequest,
    UnifiedChatResponse,
    UnifiedStreamResponse,
    UnifiedMessage,
    TokenUsage,
    ProviderType,
    MessageRole
)


class ClaudeProvider(BaseModelProvider):
    """Claude 模型提供商实现
    
    实现 Anthropic Claude 系列模型的统一接口，包括：
    - Claude 3 Haiku
    - Claude 3 Sonnet
    - Claude 3 Opus
    - Claude 3.5 Sonnet
    """

    def __init__(self, config: ClaudeConfig):
        """初始化 Claude 提供商
        
        Args:
            config: Claude 配置对象
        """
        super().__init__(config)
        self.claude_config = config

    def _get_provider_type(self) -> ProviderType:
        """获取提供商类型"""
        return ProviderType.CLAUDE

    def _validate_config(self) -> None:
        """验证配置"""
        if not self.claude_config.api_key:
            raise ValueError("Claude API key is required")

    def _initialize_client(self) -> None:
        """初始化 Claude 客户端"""
        self.client = httpx.AsyncClient(
            base_url=self.claude_config.base_url or "https://api.anthropic.com",
            headers={
                "x-api-key": self.claude_config.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            timeout=self.claude_config.timeout
        )

    def _convert_to_claude_messages(self, messages: List[UnifiedMessage]) -> List[Dict[str, str]]:
        """将统一消息格式转换为 Claude 格式
        
        Claude 有特殊的消息格式要求：
        1. 系统消息需要单独处理
        2. 消息必须交替出现（user -> assistant -> user...）
        
        Args:
            messages: 统一消息列表
            
        Returns:
            Claude 格式的消息列表和系统提示
        """
        claude_messages = []
        system_prompt = ""
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                # Claude 的系统消息单独处理
                system_prompt = msg.content
            else:
                claude_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        
        return claude_messages, system_prompt

    async def _call_api(self, request: UnifiedChatRequest) -> UnifiedChatResponse:
        """调用 Claude API
        
        Args:
            request: 统一聊天请求
            
        Returns:
            统一聊天响应
        """
        # 转换消息格式
        claude_messages, system_prompt = self._convert_to_claude_messages(request.messages)
        
        # 构建 Claude API 参数
        api_params = {
            "model": request.model,
            "messages": claude_messages,
            "max_tokens": request.max_tokens or 1000,
            "temperature": request.temperature,
            "stream": False
        }
        
        # 添加系统提示
        if system_prompt:
            api_params["system"] = system_prompt
        
        # 添加可选参数
        if request.top_p:
            api_params["top_p"] = request.top_p
        if request.stop:
            api_params["stop_sequences"] = request.stop if isinstance(request.stop, list) else [request.stop]
        
        # 添加扩展参数
        api_params.update(request.extra_params)
        
        # 调用 Claude API
        response = await self.client.post("/v1/messages", json=api_params)
        response.raise_for_status()
        
        data = response.json()
        
        # 构造统一响应
        return UnifiedChatResponse(
            id=data.get("id", str(uuid.uuid4())),
            content=data["content"][0]["text"] if data.get("content") else "",
            model=data.get("model", request.model),
            provider=ProviderType.CLAUDE,
            usage=TokenUsage(
                prompt_tokens=data.get("usage", {}).get("input_tokens", 0),
                completion_tokens=data.get("usage", {}).get("output_tokens", 0),
                total_tokens=data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)
            ),
            finish_reason=data.get("stop_reason", "stop")
        )

    async def _call_stream_api(self, request: UnifiedChatRequest) -> AsyncGenerator[UnifiedStreamResponse, None]:
        """调用 Claude 流式 API
        
        Args:
            request: 统一聊天请求
            
        Yields:
            统一流式响应
        """
        # 转换消息格式
        claude_messages, system_prompt = self._convert_to_claude_messages(request.messages)
        
        # 构建 Claude API 参数
        api_params = {
            "model": request.model,
            "messages": claude_messages,
            "max_tokens": request.max_tokens or 1000,
            "temperature": request.temperature,
            "stream": True
        }
        
        # 添加系统提示
        if system_prompt:
            api_params["system"] = system_prompt
        
        # 添加可选参数
        if request.top_p:
            api_params["top_p"] = request.top_p
        if request.stop:
            api_params["stop_sequences"] = request.stop if isinstance(request.stop, list) else [request.stop]
        
        # 添加扩展参数
        api_params.update(request.extra_params)
        
        response_id = str(uuid.uuid4())
        
        # 调用 Claude 流式 API
        async with self.client.stream("POST", "/v1/messages", json=api_params) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        import json
                        data = json.loads(line[6:])  # 去掉 "data: " 前缀
                        
                        if data.get("type") == "content_block_delta":
                            delta = data.get("delta", {}).get("text", "")
                            if delta:
                                yield UnifiedStreamResponse(
                                    id=response_id,
                                    delta=delta,
                                    model=request.model,
                                    provider=ProviderType.CLAUDE,
                                    finish_reason=None
                                )
                        elif data.get("type") == "message_stop":
                            yield UnifiedStreamResponse(
                                id=response_id,
                                delta="",
                                model=request.model,
                                provider=ProviderType.CLAUDE,
                                finish_reason="stop"
                            )
                    except Exception as e:
                        self.logger.warning(f"Failed to parse stream data: {e}")
                        continue

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if hasattr(self, 'client'):
            await self.client.aclose()


# 注册提供商
provider_registry.register(
    ProviderType.CLAUDE,
    ClaudeProvider,
    ClaudeConfig
)
