#!/bin/bash

# AI聊天系统部署脚本
# 用于快速启动和部署重构后的FastAPI系统

set -e

echo "🚀 AI聊天系统部署脚本"
echo "=========================="

# 检查Python版本
echo "📋 检查Python环境..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "Python版本: $python_version"

# 检查依赖
echo "📦 检查依赖包..."
if ! python3 -c "import fastapi, uvicorn, pydantic" 2>/dev/null; then
    echo "⚠️  缺少必要依赖，正在安装..."
    pip3 install fastapi uvicorn pydantic
else
    echo "✅ 依赖包检查通过"
fi

# 检查端口
echo "🔍 检查端口占用..."
if lsof -i :8001 >/dev/null 2>&1; then
    echo "⚠️  端口8001已被占用，正在终止..."
    lsof -ti :8001 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# 启动服务
echo "🎯 启动AI聊天系统..."
echo "服务地址: http://localhost:8001"
echo "API文档: http://localhost:8001/docs"
echo "按 Ctrl+C 停止服务"
echo "=========================="

# 启动FastAPI服务
python3 main.py
