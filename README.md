# 统一AI聊天系统

一个支持多AI服务提供商的统一聊天接口系统，提供标准化的API和会话管理功能。

## 🚀 项目特性

- **多AI提供商支持**: 统一接口支持OpenAI、Qwen、Dify等多个AI服务
- **会话管理**: 完整的会话创建、存储和管理功能
- **流式响应**: 支持实时流式聊天响应
- **用户系统**: 完整的用户认证和权限管理
- **配置管理**: 灵活的环境配置和AI提供商配置
- **缓存优化**: Redis缓存提升响应性能
- **API限流**: 防止滥用的限流机制
- **监控日志**: 完整的日志记录和监控体系

## 🏗️ 系统架构

系统采用分层架构设计，严格遵循SOLID、DRY、KISS原则：

```
┌─────────────────┐
│   前端应用层     │
├─────────────────┤
│   API网关层     │  ← 认证、限流、日志
├─────────────────┤
│   业务逻辑层     │  ← 聊天服务、会话管理
├─────────────────┤
│   AI适配器层     │  ← OpenAI、Qwen、Dify适配器
├─────────────────┤
│   数据访问层     │  ← 仓库模式、缓存
├─────────────────┤
│   数据存储层     │  ← MySQL、Redis
└─────────────────┘
```

详细架构说明请参考 [ARCHITECTURE.md](ARCHITECTURE.md)

## 📋 技术栈

- **后端框架**: Flask 3.1+
- **数据库**: MySQL 8.0+
- **缓存**: Redis 6.0+
- **Python版本**: 3.13+
- **依赖管理**: uv
- **容器化**: Docker & Docker Compose
- **API文档**: OpenAPI 3.0

## 🛠️ 快速开始

### 环境要求

- Python 3.13+
- MySQL 8.0+
- Redis 6.0+
- Docker (可选)

### 1. 克隆项目

```bash
git clone <repository-url>
cd ai
```

### 2. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

### 3. 安装依赖

```bash
# 使用uv安装依赖
uv sync

# 或使用pip
pip install -r requirements.txt
```

### 4. 数据库初始化

```bash
# 初始化数据库
python scripts/init_db.py

# 运行迁移
python scripts/migrate.py
```

### 5. 启动服务

```bash
# 开发模式
python app.py

# 生产模式
gunicorn -c gunicorn.conf.py wsgi:app
```

### 6. Docker部署 (推荐)

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

## 📖 API文档

### 基础信息

- **Base URL**: `http://localhost:3000/api/v1`
- **认证方式**: Bearer Token
- **响应格式**: JSON

### 核心接口

#### 1. 创建会话

```http
POST /api/v1/sessions
Content-Type: application/json
Authorization: Bearer <token>

{
    "title": "新的聊天会话",
    "ai_provider": "openai",
    "model": "gpt-3.5-turbo",
    "config": {
        "temperature": 0.7,
        "max_tokens": 2000
    }
}
```

#### 2. 发送消息

```http
POST /api/v1/chat
Content-Type: application/json
Authorization: Bearer <token>

{
    "session_id": "sess_123",
    "message": "你好，请介绍一下自己",
    "stream": false
}
```

#### 3. 流式聊天

```http
POST /api/v1/chat/stream
Content-Type: application/json
Authorization: Bearer <token>

{
    "session_id": "sess_123",
    "message": "请写一首诗"
}
```

完整API文档请参考 [docs/api.md](docs/api.md)

## 🔧 配置说明

### 环境变量配置

```bash
# 应用配置
FLASK_ENV=development
SECRET_KEY=your-secret-key
DEBUG=true

# 数据库配置
DATABASE_URL=mysql://user:password@localhost:3306/ai_chat
REDIS_URL=redis://localhost:6379/0

# AI提供商配置
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1

QWEN_API_KEY=xxx
QWEN_BASE_URL=https://dashscope.aliyuncs.com/api/v1

DIFY_API_KEY=xxx
DIFY_BASE_URL=https://api.dify.ai/v1
```

### AI提供商配置

系统支持通过配置文件或环境变量配置多个AI提供商：

```python
AI_PROVIDERS = {
    'openai': {
        'adapter_class': 'adapters.openai_adapter.OpenAIAdapter',
        'config': {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'base_url': os.getenv('OPENAI_BASE_URL'),
            'models': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']
        }
    },
    'qwen': {
        'adapter_class': 'adapters.qwen_adapter.QwenAdapter',
        'config': {
            'api_key': os.getenv('QWEN_API_KEY'),
            'base_url': os.getenv('QWEN_BASE_URL'),
            'models': ['qwen-turbo', 'qwen-plus', 'qwen-max']
        }
    }
}
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

### 测试配置

测试使用独立的测试数据库和配置：

```bash
# 测试环境变量
export FLASK_ENV=testing
export DATABASE_URL=mysql://user:password@localhost:3306/ai_chat_test
```

## 📊 监控和日志

### 日志配置

系统使用结构化日志记录：

```python
# 日志级别
LOGGING_LEVEL = 'INFO'

# 日志格式
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 日志文件
LOG_FILE = 'logs/app.log'
```

### 监控指标

- API响应时间
- 错误率统计
- 数据库连接池状态
- 缓存命中率
- AI提供商调用统计

## 🚀 部署指南

### 生产环境部署

1. **环境准备**
   ```bash
   # 创建生产环境配置
   cp .env.example .env.production

   # 配置生产环境变量
   export FLASK_ENV=production
   ```

2. **数据库迁移**
   ```bash
   python scripts/migrate.py --env=production
   ```

3. **启动服务**
   ```bash
   # 使用Gunicorn启动
   gunicorn -c gunicorn.conf.py wsgi:app

   # 或使用Docker
   docker-compose -f docker-compose.prod.yml up -d
   ```

详细部署说明请参考 [docs/deployment.md](docs/deployment.md)

## 🤝 开发指南

### 代码规范

- 遵循PEP 8代码风格
- 使用类型注解
- 编写单元测试
- 添加适当的文档字符串

### 提交规范

```bash
# 提交格式
git commit -m "feat: 添加新的AI适配器"
git commit -m "fix: 修复会话创建bug"
git commit -m "docs: 更新API文档"
```

### 开发流程

1. Fork项目
2. 创建功能分支
3. 编写代码和测试
4. 提交Pull Request

详细开发指南请参考 [docs/development.md](docs/development.md)

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙋‍♂️ 支持

如有问题或建议，请：

1. 查看 [FAQ](docs/faq.md)
2. 提交 [Issue](issues)
3. 发送邮件至 support@example.com

## 🗺️ 路线图

- [ ] 支持更多AI提供商
- [ ] 添加插件系统
- [ ] 实现多模态支持
- [ ] 添加Web界面
- [ ] 支持集群部署
- [ ] 添加API网关集成