#!/bin/bash
# Docker 容器启动入口脚本

set -e

echo "MCS Listener Service - Starting..."

# 检查数据库连接
if [ -z "$DB_DSN" ]; then
    echo "Error: DB_DSN environment variable is not set"
    exit 1
fi

# 等待数据库就绪（可选，如果数据库在同一网络中）
# 可以添加数据库连接检查逻辑

# 运行数据库迁移
echo "Running database migrations..."
alembic upgrade head

# 启动服务
echo "Starting service..."
exec uvicorn mcs_listener.api.main:app --host 0.0.0.0 --port 8001
