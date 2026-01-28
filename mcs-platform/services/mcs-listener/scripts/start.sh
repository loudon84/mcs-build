#!/bin/bash
# MCS Listener Service 启动脚本

set -e

echo "Starting MCS Listener Service..."

# 检查环境变量
if [ -z "$DB_DSN" ]; then
    echo "Error: DB_DSN environment variable is not set"
    exit 1
fi

# 运行数据库迁移
echo "Running database migrations..."
alembic upgrade head

# 启动服务
echo "Starting service..."
exec uvicorn mcs_listener.api.main:app --host 0.0.0.0 --port 8001
