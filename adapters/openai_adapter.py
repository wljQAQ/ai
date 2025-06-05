"""
OpenAI适配器实现
"""
import asyncio
import json
from typing import Dict, List, AsyncGenerator, Any
import aiohttp
from .base import (
    BaseAIAdapter, ChatRequest, ChatResponse, ChatMessage, MessageRole,
    UsageInfo, AdapterError, AuthenticationError, RateLimitError,
    adapter_registry
)


class OpenAIAdapter(BaseAIAdapter):
    """OpenAI适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = self._get_config_value('api_key')
        self.base_url = self._get_config_value('base_url', 'https://api.openai.com/v1')
        self.timeout = self._get_config_value('timeout', 30)
        self.max_retries = self._get_config_value('max_retries', 3)
        self.models = self._get_config_value('models', ['gpt-3.5-turbo', 'gpt-4'])
        
        # 确保base_url以/结尾
        if not self.base_url.endswith('/'):
            self.base_url += '/'
    
    def _get_provider_name(self) -> str:
        """获取提供商名称"""
        return "openai"
    
    def _validate_config(self) -> None:
        """验证配置"""
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        if not self.base_url:
            raise ValueError("OpenAI base URL is required")
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return self.models.copy()
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'AI-Chat-System/1.0'
        }
    
    def _prepare_request_data(self, request: ChatRequest) -> Dict[str, Any]:
        """准备请求数据"""
        data = {
            'model': request.model or self.models[0],
            'messages': self._prepare_messages(request.messages),
            'stream': request.stream
        }
        
        # 添加可选参数
        if request.temperature is not None:
            data['temperature'] = request.temperature
        
        if request.max_tokens is not None:
            data['max_tokens'] = request.max_tokens
        
        return data
    
    def _parse_usage(self, usage_data: Dict[str, Any]) -> UsageInfo:
        """解析使用信息"""
        return UsageInfo(
            prompt_tokens=usage_data.get('prompt_tokens', 0),
            completion_tokens=usage_data.get('completion_tokens', 0),
            total_tokens=usage_data.get('total_tokens', 0)
        )
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """同步聊天接口"""
        self._log_request(request)
        
        url = f"{self.base_url}chat/completions"
        data = self._prepare_request_data(request)
        data['stream'] = False  # 确保非流式
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    async with session.post(url, headers=self._get_headers(), json=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            return self._parse_response(result, request)
                        else:
                            await self._handle_http_error(response)
            
            except asyncio.TimeoutError:
                if attempt == self.max_retries - 1:
                    raise AdapterError(f"Request timeout after {self.max_retries} attempts", provider=self.provider_name)
                await asyncio.sleep(2 ** attempt)  # 指数退避
            
            except Exception as e:
                if attempt == self.max_retries - 1:
                    await self._handle_error(e, "Chat request failed")
                await asyncio.sleep(2 ** attempt)
    
    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[ChatResponse, None]:
        """流式聊天接口"""
        self._log_request(request)
        
        url = f"{self.base_url}chat/completions"
        data = self._prepare_request_data(request)
        data['stream'] = True  # 确保流式
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    async with session.post(url, headers=self._get_headers(), json=data) as response:
                        if response.status == 200:
                            async for chunk in self._parse_stream_response(response, request):
                                yield chunk
                            return
                        else:
                            await self._handle_http_error(response)
            
            except asyncio.TimeoutError:
                if attempt == self.max_retries - 1:
                    raise AdapterError(f"Stream request timeout after {self.max_retries} attempts", provider=self.provider_name)
                await asyncio.sleep(2 ** attempt)
            
            except Exception as e:
                if attempt == self.max_retries - 1:
                    await self._handle_error(e, "Stream chat request failed")
                await asyncio.sleep(2 ** attempt)
    
    def _parse_response(self, data: Dict[str, Any], request: ChatRequest) -> ChatResponse:
        """解析响应数据"""
        choice = data['choices'][0]
        message_data = choice['message']
        
        # 创建消息
        message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=message_data['content']
        )
        
        # 解析使用信息
        usage = None
        if 'usage' in data:
            usage = self._parse_usage(data['usage'])
        
        response = ChatResponse(
            message=message,
            usage=usage,
            model=data.get('model'),
            finish_reason=choice.get('finish_reason'),
            provider=self.provider_name,
            request_id=data.get('id')
        )
        
        self._log_response(response)
        return response
    
    async def _parse_stream_response(self, response: aiohttp.ClientResponse, request: ChatRequest) -> AsyncGenerator[ChatResponse, None]:
        """解析流式响应"""
        content_buffer = ""
        
        async for line in response.content:
            line = line.decode('utf-8').strip()
            
            if not line or not line.startswith('data: '):
                continue
            
            data_str = line[6:]  # 移除 'data: ' 前缀
            
            if data_str == '[DONE]':
                break
            
            try:
                data = json.loads(data_str)
                choice = data['choices'][0]
                
                if 'delta' in choice and 'content' in choice['delta']:
                    content = choice['delta']['content']
                    content_buffer += content
                    
                    # 创建增量响应
                    message = ChatMessage(
                        role=MessageRole.ASSISTANT,
                        content=content
                    )
                    
                    yield ChatResponse(
                        message=message,
                        model=data.get('model'),
                        finish_reason=choice.get('finish_reason'),
                        provider=self.provider_name,
                        request_id=data.get('id')
                    )
                
                # 如果是最后一个chunk，包含完整信息
                if choice.get('finish_reason'):
                    final_message = ChatMessage(
                        role=MessageRole.ASSISTANT,
                        content=content_buffer
                    )
                    
                    usage = None
                    if 'usage' in data:
                        usage = self._parse_usage(data['usage'])
                    
                    final_response = ChatResponse(
                        message=final_message,
                        usage=usage,
                        model=data.get('model'),
                        finish_reason=choice.get('finish_reason'),
                        provider=self.provider_name,
                        request_id=data.get('id')
                    )
                    
                    self._log_response(final_response)
                    yield final_response
            
            except json.JSONDecodeError:
                continue
    
    async def _handle_http_error(self, response: aiohttp.ClientResponse) -> None:
        """处理HTTP错误"""
        try:
            error_data = await response.json()
            error_message = error_data.get('error', {}).get('message', f"HTTP {response.status}")
        except:
            error_message = f"HTTP {response.status}"
        
        if response.status == 401:
            raise AuthenticationError(f"Authentication failed: {error_message}", provider=self.provider_name)
        elif response.status == 429:
            raise RateLimitError(f"Rate limit exceeded: {error_message}", provider=self.provider_name)
        else:
            raise AdapterError(f"API request failed: {error_message}", provider=self.provider_name)


# 注册适配器
adapter_registry.register('openai', OpenAIAdapter)
