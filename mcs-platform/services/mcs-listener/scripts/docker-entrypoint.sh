#!/bin/bash
# Docker 容器启动入口脚本

set -e

echo "MCS Listener Service - Starting..."

# 加载 .env 文件（如果存在，Docker 中通常不需要）
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    set -a
    source .env
    set +a
fi

# 检查数据库连接
if [ -z "$DB_DSN" ]; then
    echo "Error: DB_DSN environment variable is not set"
    echo "Please set DB_DSN in .env file or as an environment variable"
    exit 1
fi

# 设置 PYTHONPATH 以包含 src 目录
export PYTHONPATH="${PYTHONPATH}:/app/src"

# 等待数据库就绪（可选，如果数据库在同一网络中）
# 可以添加数据库连接检查逻辑

# 运行数据库迁移
echo "Running database migrations..."
alembic upgrade head

# 启动服务
echo "Starting service..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8001
