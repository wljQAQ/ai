"""
Pydantic vs Dataclasses 对比示例
用于展示在 AI 聊天系统中的差异
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import json


# ============= Pydantic 方案 =============
class OpenAIConfigPydantic(BaseModel):
    """使用 Pydantic 的配置模型"""
    api_key: str = Field(..., description="OpenAI API密钥", min_length=1)
    base_url: Optional[str] = Field(default=None, description="API基础URL")
    models: List[str] = Field(
        default=['gpt-3.5-turbo', 'gpt-4'], 
        description="支持的模型列表",
        min_items=1
    )
    timeout: float = Field(default=30.0, ge=1.0, le=300.0, description="请求超时时间(秒)")
    max_retries: int = Field(default=3, ge=0, le=10, description="最大重试次数")
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        if not v.startswith('sk-'):
            raise ValueError('OpenAI API key must start with "sk-"')
        return v
    
    @field_validator('models')
    @classmethod
    def validate_models(cls, v):
        valid_models = {
            'gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 
            'gpt-4', 'gpt-4-turbo', 'gpt-4-32k',
            'gpt-4o', 'gpt-4o-mini'
        }
        for model in v:
            if model not in valid_models:
                raise ValueError(f'Unsupported model: {model}')
        return v


# ============= Dataclasses 方案 =============
@dataclass
class OpenAIConfigDataclass:
    """使用 Dataclasses 的配置模型"""
    api_key: str
    base_url: Optional[str] = None
    models: List[str] = field(default_factory=lambda: ['gpt-3.5-turbo', 'gpt-4'])
    timeout: float = 30.0
    max_retries: int = 3
    
    def __post_init__(self):
        """手动验证逻辑"""
        # 验证 API key
        if not self.api_key:
            raise ValueError("API key is required")
        if not self.api_key.startswith('sk-'):
            raise ValueError('OpenAI API key must start with "sk-"')
        
        # 验证 models
        if not self.models:
            raise ValueError("At least one model is required")
        
        valid_models = {
            'gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 
            'gpt-4', 'gpt-4-turbo', 'gpt-4-32k',
            'gpt-4o', 'gpt-4o-mini'
        }
        for model in self.models:
            if model not in valid_models:
                raise ValueError(f'Unsupported model: {model}')
        
        # 验证数值范围
        if not (1.0 <= self.timeout <= 300.0):
            raise ValueError("Timeout must be between 1.0 and 300.0")
        if not (0 <= self.max_retries <= 10):
            raise ValueError("Max retries must be between 0 and 10")
    
    def to_dict(self) -> Dict[str, Any]:
        """手动序列化"""
        return {
            'api_key': self.api_key,
            'base_url': self.base_url,
            'models': self.models,
            'timeout': self.timeout,
            'max_retries': self.max_retries
        }
    
    def to_json(self) -> str:
        """手动 JSON 序列化"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OpenAIConfigDataclass':
        """手动反序列化"""
        return cls(
            api_key=data['api_key'],
            base_url=data.get('base_url'),
            models=data.get('models', ['gpt-3.5-turbo', 'gpt-4']),
            timeout=data.get('timeout', 30.0),
            max_retries=data.get('max_retries', 3)
        )


# ============= 使用示例和对比 =============
def demonstrate_differences():
    """演示两种方案的差异"""
    
    print("=== Pydantic vs Dataclasses 对比 ===\n")
    
    # 测试数据
    valid_config = {
        "api_key": "sk-test123456789",
        "models": ["gpt-3.5-turbo", "gpt-4"],
        "timeout": 60.0,
        "max_retries": 5
    }
    
    invalid_config = {
        "api_key": "invalid-key",  # 不以 sk- 开头
        "models": ["invalid-model"],  # 不支持的模型
        "timeout": 500.0,  # 超出范围
        "max_retries": 20  # 超出范围
    }
    
    print("1. 创建有效配置:")
    print("-" * 40)
    
    # Pydantic
    try:
        pydantic_config = OpenAIConfigPydantic(**valid_config)
        print("✅ Pydantic: 创建成功")
        print(f"   JSON: {pydantic_config.model_dump_json()}")
    except Exception as e:
        print(f"❌ Pydantic: {e}")
    
    # Dataclasses
    try:
        dataclass_config = OpenAIConfigDataclass(**valid_config)
        print("✅ Dataclasses: 创建成功")
        print(f"   JSON: {dataclass_config.to_json()}")
    except Exception as e:
        print(f"❌ Dataclasses: {e}")
    
    print("\n2. 创建无效配置:")
    print("-" * 40)
    
    # Pydantic
    try:
        pydantic_config = OpenAIConfigPydantic(**invalid_config)
        print("✅ Pydantic: 创建成功")
    except Exception as e:
        print(f"❌ Pydantic: {e}")
    
    # Dataclasses
    try:
        dataclass_config = OpenAIConfigDataclass(**invalid_config)
        print("✅ Dataclasses: 创建成功")
    except Exception as e:
        print(f"❌ Dataclasses: {e}")
    
    print("\n3. 类型转换测试:")
    print("-" * 40)
    
    # 测试自动类型转换
    string_config = {
        "api_key": "sk-test123456789",
        "timeout": "60",  # 字符串
        "max_retries": "5"  # 字符串
    }
    
    # Pydantic (自动类型转换)
    try:
        pydantic_config = OpenAIConfigPydantic(**string_config)
        print("✅ Pydantic: 自动类型转换成功")
        print(f"   timeout类型: {type(pydantic_config.timeout)}")
        print(f"   max_retries类型: {type(pydantic_config.max_retries)}")
    except Exception as e:
        print(f"❌ Pydantic: {e}")
    
    # Dataclasses (需要手动转换)
    try:
        # 需要手动转换类型
        converted_config = {
            "api_key": string_config["api_key"],
            "timeout": float(string_config["timeout"]),
            "max_retries": int(string_config["max_retries"])
        }
        dataclass_config = OpenAIConfigDataclass(**converted_config)
        print("✅ Dataclasses: 手动类型转换成功")
    except Exception as e:
        print(f"❌ Dataclasses: {e}")


if __name__ == "__main__":
    demonstrate_differences()
