# 部署指南

## 部署架构

### 生产环境架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │      Nginx      │    │   Application   │
│    (Optional)   │────│  Reverse Proxy  │────│    Instances    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │      Redis      │    │      MySQL      │
                       │     Cache       │    │    Database     │
                       └─────────────────┘    └─────────────────┘
```

## 部署方式

### 1. Docker部署 (推荐)

#### 1.1 准备环境

```bash
# 安装Docker和Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 1.2 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑生产环境配置
vim .env
```

重要配置项：
```bash
# 应用配置
FLASK_ENV=production
SECRET_KEY=your-production-secret-key
DEBUG=false

# 数据库配置
DATABASE_URL=mysql://ai_user:strong_password@mysql:3306/ai_chat

# AI提供商配置
OPENAI_API_KEY=your-openai-api-key
QWEN_API_KEY=your-qwen-api-key
DIFY_API_KEY=your-dify-api-key
```

#### 1.3 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

#### 1.4 初始化数据库

```bash
# 进入应用容器
docker-compose exec app bash

# 运行数据库初始化脚本
python scripts/init_db.py

# 运行数据库迁移
python scripts/migrate.py
```

### 2. 传统部署

#### 2.1 系统要求

- Ubuntu 20.04+ / CentOS 8+
- Python 3.13+
- MySQL 8.0+
- Redis 6.0+
- Nginx 1.18+

#### 2.2 安装依赖

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python 3.13
sudo apt install python3.13 python3.13-venv python3.13-dev

# 安装MySQL
sudo apt install mysql-server mysql-client

# 安装Redis
sudo apt install redis-server

# 安装Nginx
sudo apt install nginx
```

#### 2.3 配置数据库

```bash
# 登录MySQL
sudo mysql -u root -p

# 创建数据库和用户
CREATE DATABASE ai_chat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ai_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON ai_chat.* TO 'ai_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 2.4 部署应用

```bash
# 创建应用目录
sudo mkdir -p /opt/ai-chat
cd /opt/ai-chat

# 克隆代码
git clone <repository-url> .

# 创建虚拟环境
python3.13 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
vim .env

# 初始化数据库
python scripts/init_db.py

# 创建日志目录
mkdir -p logs

# 设置权限
sudo chown -R www-data:www-data /opt/ai-chat
```

#### 2.5 配置Systemd服务

创建服务文件：
```bash
sudo vim /etc/systemd/system/ai-chat.service
```

内容：
```ini
[Unit]
Description=AI Chat System
After=network.target mysql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/ai-chat
Environment=PATH=/opt/ai-chat/venv/bin
ExecStart=/opt/ai-chat/venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-chat
sudo systemctl start ai-chat
sudo systemctl status ai-chat
```

#### 2.6 配置Nginx

创建Nginx配置：
```bash
sudo vim /etc/nginx/sites-available/ai-chat
```

内容：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL配置
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # 代理配置
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 流式响应配置
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # 静态文件
    location /static/ {
        alias /opt/ai-chat/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 健康检查
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:3000;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/ai-chat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 监控和维护

### 1. 日志管理

```bash
# 查看应用日志
tail -f /opt/ai-chat/logs/app.log

# 查看系统服务日志
sudo journalctl -u ai-chat -f

# 查看Nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. 性能监控

#### 2.1 系统监控

```bash
# 安装监控工具
sudo apt install htop iotop nethogs

# 监控系统资源
htop
iotop
nethogs
```

#### 2.2 应用监控

```bash
# 检查应用状态
curl http://localhost:3000/health

# 监控数据库连接
mysql -u ai_user -p -e "SHOW PROCESSLIST;"

# 监控Redis
redis-cli info stats
```

### 3. 备份策略

#### 3.1 数据库备份

```bash
# 创建备份脚本
sudo vim /opt/scripts/backup_db.sh
```

内容：
```bash
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="ai_chat"
DB_USER="ai_user"
DB_PASS="strong_password"

mkdir -p $BACKUP_DIR

# 备份数据库
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME > $BACKUP_DIR/ai_chat_$DATE.sql

# 压缩备份文件
gzip $BACKUP_DIR/ai_chat_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "ai_chat_*.sql.gz" -mtime +7 -delete

echo "Database backup completed: ai_chat_$DATE.sql.gz"
```

设置定时备份：
```bash
sudo chmod +x /opt/scripts/backup_db.sh
sudo crontab -e

# 添加每日凌晨2点备份
0 2 * * * /opt/scripts/backup_db.sh
```

#### 3.2 应用备份

```bash
# 备份应用代码和配置
tar -czf /opt/backups/ai-chat-$(date +%Y%m%d).tar.gz \
    --exclude='venv' \
    --exclude='logs' \
    --exclude='__pycache__' \
    /opt/ai-chat
```

### 4. 更新部署

```bash
# 拉取最新代码
cd /opt/ai-chat
git pull origin main

# 激活虚拟环境
source venv/bin/activate

# 更新依赖
pip install -r requirements.txt

# 运行数据库迁移
python scripts/migrate.py

# 重启服务
sudo systemctl restart ai-chat

# 检查服务状态
sudo systemctl status ai-chat
```

## 故障排除

### 1. 常见问题

#### 应用无法启动
```bash
# 检查日志
sudo journalctl -u ai-chat -n 50

# 检查配置
python -c "from config.base import BaseConfig; print(BaseConfig.validate_config())"

# 检查端口占用
sudo netstat -tlnp | grep :3000
```

#### 数据库连接失败
```bash
# 测试数据库连接
mysql -u ai_user -p ai_chat

# 检查数据库服务
sudo systemctl status mysql
```

#### Redis连接失败
```bash
# 测试Redis连接
redis-cli ping

# 检查Redis服务
sudo systemctl status redis
```

### 2. 性能优化

#### 数据库优化
```sql
-- 查看慢查询
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';

-- 分析查询性能
EXPLAIN SELECT * FROM sessions WHERE user_id = 'xxx';
```

#### 缓存优化
```bash
# 监控Redis内存使用
redis-cli info memory

# 查看缓存命中率
redis-cli info stats | grep keyspace
```

## 安全配置

### 1. 防火墙配置

```bash
# 安装UFW
sudo apt install ufw

# 配置防火墙规则
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# 启用防火墙
sudo ufw enable
```

### 2. SSL证书

```bash
# 使用Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加：0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. 安全加固

```bash
# 禁用root SSH登录
sudo vim /etc/ssh/sshd_config
# 设置：PermitRootLogin no

# 配置fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```
