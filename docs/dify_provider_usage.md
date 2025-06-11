# Dify 提供商使用指南

## 概述

Dify 提供商实现了对 Dify AI 平台的统一接口适配，支持：

- 对话补全接口 (chat completions)
- 流式响应支持
- 错误处理和重试机制
- 对话状态管理
- 与项目现有架构的完全兼容

## 快速开始

### 1. 配置 Dify 提供商

```python
from models.schemas.ai_provider import DifyConfig

config = DifyConfig(
    api_key="your-dify-api-key",
    base_url="https://api.dify.ai",  # 或您的私有部署地址
    default_model="gpt-3.5-turbo",
    timeout=30.0,
    max_retries=3,
    conversation_id="optional-conversation-id"  # 可选，用于维持对话状态
)
```

### 2. 创建提供商实例

```python
from core.model_providers import provider_registry
from models.schemas.ai_provider import ProviderType

provider = provider_registry.create_provider(
    ProviderType.DIFY,
    config.model_dump()
)
```

### 3. 发送聊天请求

```python
from models.schemas.ai_provider import (
    UnifiedChatRequest,
    UnifiedMessage,
    MessageRole
)

# 创建聊天请求
request = UnifiedChatRequest(
    messages=[
        UnifiedMessage(
            role=MessageRole.SYSTEM,
            content="你是一个有用的AI助手。"
        ),
        UnifiedMessage(
            role=MessageRole.USER,
            content="你好，请介绍一下你自己。"
        )
    ],
    model="gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=1000
)

# 发送请求
response = await provider.chat(request)
print(f"回复: {response.content}")
```

### 4. 流式响应

```python
# 启用流式响应
request.stream = True

async for chunk in provider.chat_stream(request):
    print(chunk.delta, end="", flush=True)
    if chunk.finish_reason:
        print(f"\n完成，原因: {chunk.finish_reason}")
        break
```

## 配置选项

### DifyConfig 参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `api_key` | str | ✅ | - | Dify API 密钥 |
| `base_url` | str | ❌ | "https://api.dify.ai" | API 基础URL |
| `default_model` | str | ❌ | "gpt-3.5-turbo" | 默认模型 |
| `timeout` | float | ❌ | 30.0 | 请求超时时间(秒) |
| `max_retries` | int | ❌ | 3 | 最大重试次数 |
| `retry_delay` | float | ❌ | 1.0 | 重试延迟(秒) |
| `conversation_id` | str | ❌ | None | 对话ID |
| `app_id` | str | ❌ | None | 应用ID |

### 支持的模型

Dify 提供商支持的模型取决于您的 Dify 应用配置。常见模型包括：

- `gpt-3.5-turbo`
- `gpt-4`
- `gpt-4-turbo`
- `claude-3-haiku`
- `claude-3-sonnet`
- `claude-3-opus`

## API 格式转换

### 消息格式转换

Dify API 使用不同于 OpenAI 的消息格式：

**输入（统一格式）:**
```python
messages = [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"},
    {"role": "user", "content": "今天天气怎么样？"}
]
```

**转换为 Dify 格式:**
```python
{
    "query": "今天天气怎么样？",  # 最后一条用户消息
    "inputs": "你是一个助手",    # 系统消息作为输入
    "conversation_id": "...",   # 对话ID（可选）
    "user": "user-123"          # 用户标识
}
```

### 响应格式转换

**Dify 响应:**
```json
{
    "id": "msg-123",
    "answer": "今天天气很好...",
    "conversation_id": "conv-456",
    "metadata": {
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 20,
            "total_tokens": 70
        }
    }
}
```

**转换为统一格式:**
```python
UnifiedChatResponse(
    id="msg-123",
    content="今天天气很好...",
    model="gpt-3.5-turbo",
    provider=ProviderType.DIFY,
    usage=TokenUsage(
        prompt_tokens=50,
        completion_tokens=20,
        total_tokens=70
    ),
    finish_reason="stop",
    extra_data={
        "conversation_id": "conv-456",
        "metadata": {...}
    }
)
```

## 错误处理

Dify 提供商继承了基础提供商的错误处理机制：

```python
from models.schemas.ai_provider import ProviderError

try:
    response = await provider.chat(request)
except ProviderError as e:
    print(f"错误代码: {e.error_code}")
    print(f"错误消息: {e.error_message}")
    print(f"是否可重试: {e.is_retryable}")
    print(f"重试等待时间: {e.retry_after}")
```

## 性能监控

```python
# 获取性能指标
metrics = provider.get_metrics()
print(f"请求次数: {metrics.request_count}")
print(f"成功次数: {metrics.success_count}")
print(f"错误次数: {metrics.error_count}")
print(f"平均延迟: {metrics.avg_latency_ms}ms")
print(f"总Token数: {metrics.total_tokens}")

# 重置指标
provider.reset_metrics()
```

## 最佳实践

### 1. 对话状态管理

```python
# 为每个用户会话维护独立的对话ID
user_conversations = {}

def get_provider_for_user(user_id: str):
    if user_id not in user_conversations:
        user_conversations[user_id] = str(uuid.uuid4())
    
    config = DifyConfig(
        api_key="your-api-key",
        conversation_id=user_conversations[user_id]
    )
    return provider_registry.create_provider(ProviderType.DIFY, config.model_dump())
```

### 2. 错误重试策略

```python
config = DifyConfig(
    api_key="your-api-key",
    max_retries=3,      # 最多重试3次
    retry_delay=2.0,    # 每次重试间隔2秒
    timeout=60.0        # 单次请求超时60秒
)
```

### 3. 流式响应处理

```python
async def handle_stream_response(provider, request):
    full_content = ""
    try:
        async for chunk in provider.chat_stream(request):
            if chunk.delta:
                full_content += chunk.delta
                # 实时显示或处理增量内容
                yield chunk.delta
            
            if chunk.finish_reason:
                # 流式响应完成
                break
    except Exception as e:
        # 处理流式响应中的错误
        print(f"流式响应错误: {e}")
    
    return full_content
```

## 注意事项

1. **API Key 安全**: 请确保 Dify API key 的安全，不要在客户端代码中暴露
2. **对话状态**: Dify 使用 `conversation_id` 维持对话状态，请妥善管理
3. **模型支持**: 实际支持的模型取决于您的 Dify 应用配置
4. **速率限制**: 请遵守 Dify 平台的 API 调用频率限制
5. **错误处理**: 建议实现适当的错误处理和重试逻辑

## 故障排除

### 常见错误

1. **401 Unauthorized**: 检查 API key 是否正确
2. **404 Not Found**: 检查 base_url 是否正确
3. **429 Too Many Requests**: 降低请求频率
4. **500 Internal Server Error**: Dify 服务器错误，稍后重试

### 调试技巧

```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 查看请求详情
provider.logger.setLevel(logging.DEBUG)
```
