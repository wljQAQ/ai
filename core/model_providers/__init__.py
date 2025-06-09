# AI模型提供商模块

from .base_provider import (
    BaseModelProvider,
    ProviderRegistry,
    provider_registry
)

# 导入具体的提供商实现（这会自动注册它们）
from .openai_provider_new import OpenAIProvider
from .claude_provider import ClaudeProvider

__all__ = [
    'BaseModelProvider',
    'ProviderRegistry',
    'provider_registry',
    'OpenAIProvider',
    'ClaudeProvider'
]
