"""
OpenAI模型提供商实现
"""
from typing import Dict, List, AsyncGenerator, Any
from .base_provider import BaseModelProvider, provider_registry


class OpenAIProvider(BaseModelProvider):
    """OpenAI模型提供商"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = self._get_config_value('api_key')
        self.models = self._get_config_value('models', ['gpt-3.5-turbo', 'gpt-4'])

    def _get_provider_name(self) -> str:
        """获取提供商名称"""
        return "openai"

    def _validate_config(self) -> None:
        """验证配置"""
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return self.models.copy()

    async def chat(self, request) -> Any:
        """同步聊天接口"""
        # 简化实现，实际项目中需要调用OpenAI API
        return {"message": "Mock OpenAI response", "model": "gpt-3.5-turbo"}

    async def chat_stream(self, request) -> AsyncGenerator[Any, None]:
        """流式聊天接口"""
        # 简化实现，实际项目中需要调用OpenAI API
        yield {"message": "Mock", "model": "gpt-3.5-turbo"}
        yield {"message": " OpenAI", "model": "gpt-3.5-turbo"}
        yield {"message": " stream response", "model": "gpt-3.5-turbo"}


# 注册提供商
provider_registry.register('openai', OpenAIProvider)