# 统一AI聊天系统架构设计

## 目录结构

```
ai/
├── README.md                    # 项目说明文档
├── ARCHITECTURE.md             # 架构设计文档
├── pyproject.toml              # 项目配置和依赖
├── requirements.txt            # Python依赖列表
├── .env.example               # 环境变量示例
├── .gitignore                 # Git忽略文件
├── docker-compose.yml         # Docker编排文件
├── Dockerfile                 # Docker镜像构建文件
│
├── app.py                     # 应用入口文件
├── wsgi.py                    # WSGI服务器入口
│
├── config/                    # 配置管理
│   ├── __init__.py
│   ├── base.py               # 基础配置
│   ├── development.py        # 开发环境配置
│   ├── production.py         # 生产环境配置
│   └── testing.py            # 测试环境配置
│
├── core/                      # 核心模块
│   ├── __init__.py
│   ├── app_factory.py        # Flask应用工厂
│   ├── extensions.py         # Flask扩展初始化
│   ├── exceptions.py         # 自定义异常
│   ├── middleware.py         # 中间件
│   └── utils.py              # 工具函数
│
├── api/                       # API接口层
│   ├── __init__.py
│   ├── v1/                   # API版本1
│   │   ├── __init__.py
│   │   ├── chat.py           # 聊天相关API
│   │   ├── session.py        # 会话管理API
│   │   ├── user.py           # 用户管理API
│   │   └── health.py         # 健康检查API
│   └── middleware/           # API中间件
│       ├── __init__.py
│       ├── auth.py           # 认证中间件
│       ├── rate_limit.py     # 限流中间件
│       └── logging.py        # 日志中间件
│
├── services/                  # 业务服务层
│   ├── __init__.py
│   ├── chat_service.py       # 聊天服务
│   ├── session_service.py    # 会话服务
│   ├── user_service.py       # 用户服务
│   └── ai_service.py         # AI服务管理
│
├── adapters/                  # AI适配器层
│   ├── __init__.py
│   ├── base.py               # 基础适配器接口
│   ├── openai_adapter.py     # OpenAI适配器
│   ├── qwen_adapter.py       # Qwen适配器
│   ├── dify_adapter.py       # Dify适配器
│   └── factory.py            # 适配器工厂
│
├── models/                    # 数据模型层
│   ├── __init__.py
│   ├── base.py               # 基础模型
│   ├── user.py               # 用户模型
│   ├── session.py            # 会话模型
│   ├── message.py            # 消息模型
│   └── ai_provider.py        # AI提供商模型
│
├── repositories/              # 数据访问层
│   ├── __init__.py
│   ├── base.py               # 基础仓库
│   ├── user_repository.py    # 用户数据访问
│   ├── session_repository.py # 会话数据访问
│   └── message_repository.py # 消息数据访问
│
├── schemas/                   # 数据验证模式
│   ├── __init__.py
│   ├── chat.py               # 聊天相关模式
│   ├── session.py            # 会话相关模式
│   └── user.py               # 用户相关模式
│
├── utils/                     # 工具模块
│   ├── __init__.py
│   ├── logger.py             # 日志工具
│   ├── cache.py              # 缓存工具
│   ├── security.py           # 安全工具
│   └── validators.py         # 验证工具
│
├── migrations/                # 数据库迁移
│   └── versions/
│
├── tests/                     # 测试代码
│   ├── __init__.py
│   ├── conftest.py           # 测试配置
│   ├── unit/                 # 单元测试
│   ├── integration/          # 集成测试
│   └── fixtures/             # 测试数据
│
├── docs/                      # 文档
│   ├── api.md                # API文档
│   ├── deployment.md         # 部署文档
│   └── development.md        # 开发文档
│
└── scripts/                   # 脚本文件
    ├── init_db.py            # 数据库初始化
    ├── migrate.py            # 数据库迁移
    └── seed_data.py          # 种子数据
```

## 核心设计原则

### 1. SOLID原则
- **单一职责原则(SRP)**: 每个类只负责一个功能
- **开闭原则(OCP)**: 对扩展开放，对修改关闭
- **里氏替换原则(LSP)**: 子类可以替换父类
- **接口隔离原则(ISP)**: 接口应该小而专一
- **依赖倒置原则(DIP)**: 依赖抽象而不是具体实现

### 2. DRY原则
- 避免重复代码
- 提取公共功能到基类或工具函数
- 使用配置文件管理重复的配置项

### 3. KISS原则
- 保持代码简单易懂
- 避免过度设计
- 优先选择简单的解决方案

## 模块职责说明

### API层 (api/)
- 处理HTTP请求和响应
- 参数验证和序列化
- 路由定义和版本管理
- 中间件集成

### 服务层 (services/)
- 业务逻辑实现
- 事务管理
- 服务间协调
- 业务规则验证

### 适配器层 (adapters/)
- 统一不同AI服务商的接口
- 协议转换和数据映射
- 错误处理和重试机制
- 配置管理

### 数据层 (models/ & repositories/)
- 数据模型定义
- 数据访问抽象
- 查询优化
- 缓存策略

### 工具层 (utils/)
- 通用工具函数
- 日志记录
- 安全功能
- 性能监控
