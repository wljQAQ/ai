# AI 模型提供商架构设计文档

## 🎯 **架构概述**

本文档描述了重构后的 AI 模型提供商架构，该架构提供了统一、可扩展、类型安全的接口来管理不同的 AI 服务提供商。

## 📋 **设计目标**

1. **统一接口**：抹平不同 AI 供应商的 API 差异
2. **类型安全**：使用 Pydantic 进行配置验证和数据建模
3. **易于扩展**：支持轻松添加新的 AI 提供商
4. **错误处理**：完善的重试机制和错误处理
5. **性能监控**：内置性能指标收集和监控
6. **异步支持**：全面支持异步操作

## 🏗️ **架构组件**

### **1. 核心抽象层**

```
models/schemas/ai_provider.py
├── 统一数据模型
│   ├── UnifiedChatRequest      # 统一请求格式
│   ├── UnifiedChatResponse     # 统一响应格式
│   ├── UnifiedStreamResponse   # 统一流式响应
│   └── UnifiedMessage          # 统一消息格式
├── 配置模型
│   ├── BaseProviderConfig      # 基础配置
│   ├── OpenAIConfig           # OpenAI 配置
│   └── ClaudeConfig           # Claude 配置
└── 辅助模型
    ├── TokenUsage             # Token 使用统计
    ├── ProviderError          # 错误信息
    └── ProviderMetrics        # 性能指标
```

### **2. 基础提供商抽象**

```python
# core/model_providers/base_provider.py
class BaseModelProvider(ABC):
    """AI模型提供商抽象基类"""
    
    # 抽象方法（子类必须实现）
    @abstractmethod
    def _get_provider_type(self) -> ProviderType
    
    @abstractmethod
    def _validate_config(self) -> None
    
    @abstractmethod
    def _initialize_client(self) -> None
    
    @abstractmethod
    async def _call_api(self, request: UnifiedChatRequest) -> UnifiedChatResponse
    
    @abstractmethod
    async def _call_stream_api(self, request: UnifiedChatRequest) -> AsyncGenerator[UnifiedStreamResponse, None]
    
    # 通用方法（已实现）
    async def chat(self, request: UnifiedChatRequest) -> UnifiedChatResponse
    async def chat_stream(self, request: UnifiedChatRequest) -> AsyncGenerator[UnifiedStreamResponse, None]
    def get_metrics(self) -> ProviderMetrics
```

### **3. 具体提供商实现**

#### **OpenAI 提供商**
```python
# core/model_providers/openai_provider_new.py
class OpenAIProvider(BaseModelProvider):
    """OpenAI 模型提供商实现"""
    
    def _get_provider_type(self) -> ProviderType:
        return ProviderType.OPENAI
    
    def _initialize_client(self) -> None:
        self.client = AsyncOpenAI(...)
    
    async def _call_api(self, request: UnifiedChatRequest) -> UnifiedChatResponse:
        # OpenAI 特定的 API 调用逻辑
        pass
```

#### **Claude 提供商**
```python
# core/model_providers/claude_provider.py
class ClaudeProvider(BaseModelProvider):
    """Claude 模型提供商实现"""
    
    def _get_provider_type(self) -> ProviderType:
        return ProviderType.CLAUDE
    
    def _convert_to_claude_messages(self, messages):
        # Claude 特有的消息格式转换
        pass
```

### **4. 提供商注册表**

```python
# 自动注册机制
provider_registry.register(
    ProviderType.OPENAI,
    OpenAIProvider,
    OpenAIConfig
)

# 动态创建提供商
provider = provider_registry.create_provider(
    ProviderType.OPENAI,
    config_data
)
```

## 🔧 **核心特性**

### **1. 统一的数据格式**

所有提供商都使用相同的请求/响应格式：

```python
# 统一请求
request = UnifiedChatRequest(
    messages=[
        UnifiedMessage(role=MessageRole.USER, content="Hello")
    ],
    model="gpt-3.5-turbo",
    temperature=0.7
)

# 统一响应
response = UnifiedChatResponse(
    id="resp_123",
    content="Hello! How can I help you?",
    model="gpt-3.5-turbo",
    provider=ProviderType.OPENAI,
    usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
)
```

### **2. 类型安全的配置管理**

```python
# Pydantic 配置验证
config = OpenAIConfig(
    api_key="sk-test123",  # 自动验证格式
    timeout=30.0,          # 自动验证范围
    max_retries=3          # 自动验证范围
)
```

### **3. 完善的错误处理**

```python
# 自动重试机制
try:
    response = await provider.chat(request)
except ProviderError as e:
    print(f"错误: {e.error_message}")
    print(f"是否可重试: {e.is_retryable}")
```

### **4. 性能监控**

```python
# 获取性能指标
metrics = provider.get_metrics()
print(f"成功率: {metrics.success_count / metrics.request_count * 100:.1f}%")
print(f"平均延迟: {metrics.avg_latency_ms:.1f}ms")
```

## 🚀 **使用示例**

### **基本使用**

```python
import asyncio
from core.model_providers import provider_registry
from models.schemas.ai_provider import *

async def main():
    # 1. 创建提供商
    provider = provider_registry.create_provider(
        ProviderType.OPENAI,
        {
            "api_key": "your-api-key",
            "default_model": "gpt-3.5-turbo"
        }
    )
    
    # 2. 创建请求
    request = UnifiedChatRequest(
        messages=[
            UnifiedMessage(role=MessageRole.USER, content="Hello!")
        ],
        model="gpt-3.5-turbo"
    )
    
    # 3. 发送请求
    response = await provider.chat(request)
    print(response.content)

asyncio.run(main())
```

### **提供商切换**

```python
# 轻松切换不同提供商
providers = {
    "openai": provider_registry.create_provider(ProviderType.OPENAI, openai_config),
    "claude": provider_registry.create_provider(ProviderType.CLAUDE, claude_config)
}

# 使用相同的请求格式
for name, provider in providers.items():
    response = await provider.chat(request)
    print(f"{name}: {response.content}")
```

### **流式聊天**

```python
# 流式响应
async for chunk in provider.chat_stream(request):
    print(chunk.delta, end="", flush=True)
```

## 📈 **扩展新提供商**

添加新的 AI 提供商只需要 3 步：

### **1. 创建配置类**

```python
class NewProviderConfig(BaseProviderConfig):
    provider_type: ProviderType = Field(default=ProviderType.NEW_PROVIDER)
    special_param: str = Field(..., description="特殊参数")
```

### **2. 实现提供商类**

```python
class NewProvider(BaseModelProvider):
    def _get_provider_type(self) -> ProviderType:
        return ProviderType.NEW_PROVIDER
    
    def _initialize_client(self) -> None:
        # 初始化客户端
        pass
    
    async def _call_api(self, request: UnifiedChatRequest) -> UnifiedChatResponse:
        # 实现 API 调用
        pass
```

### **3. 注册提供商**

```python
provider_registry.register(
    ProviderType.NEW_PROVIDER,
    NewProvider,
    NewProviderConfig
)
```

## 🔍 **架构优势**

### **1. 开发体验**
- ✅ 统一的接口，学习成本低
- ✅ 类型提示和自动补全
- ✅ 详细的错误信息
- ✅ 丰富的配置验证

### **2. 可维护性**
- ✅ 清晰的职责分离
- ✅ 易于测试和调试
- ✅ 标准化的错误处理
- ✅ 完善的日志记录

### **3. 可扩展性**
- ✅ 插件化的提供商架构
- ✅ 灵活的配置系统
- ✅ 支持自定义扩展参数
- ✅ 向后兼容的设计

### **4. 生产就绪**
- ✅ 完善的错误处理和重试
- ✅ 性能监控和指标收集
- ✅ 异步支持和高并发
- ✅ 内存和资源管理

## 📝 **最佳实践**

1. **配置管理**：使用环境变量管理敏感信息
2. **错误处理**：总是捕获和处理 ProviderError
3. **性能监控**：定期检查和重置性能指标
4. **资源管理**：使用异步上下文管理器
5. **测试**：为每个提供商编写单元测试

## 🔮 **未来规划**

1. **更多提供商**：支持 Gemini、文心一言等
2. **高级功能**：函数调用、图像生成等
3. **缓存机制**：响应缓存和智能缓存策略
4. **负载均衡**：多提供商负载均衡和故障转移
5. **成本优化**：智能路由和成本控制
