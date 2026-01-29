#!/bin/bash
# MCS Listener Service 启动脚本
# 
# 使用方法：
#   1. 确保已激活 conda 环境：conda activate mcs-platform
#   2. 运行脚本：bash scripts/start.sh
#   或者
#   1. 直接运行：conda run -n mcs-platform bash scripts/start.sh

set -e

# 切换到脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Starting MCS Listener Service..."
echo "Working directory: $PROJECT_ROOT"

# 加载 .env 文件（如果存在）
ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment variables from .env file: $ENV_FILE"
    set -a  # 自动导出所有变量
    # 使用更健壮的方法加载 .env，处理 Windows 行尾符和特殊字符
    while IFS= read -r line || [ -n "$line" ]; do
        # 移除 Windows 行尾符和前后空格
        line=$(echo "$line" | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        # 跳过注释和空行
        if [[ -z "$line" ]] || [[ "$line" =~ ^# ]]; then
            continue
        fi
        # 检查是否是有效的变量赋值格式
        if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
            export "$line"
        fi
    done < "$ENV_FILE"
    set +a  # 关闭自动导出
else
    echo "Warning: .env file not found at $ENV_FILE"
fi

# 检查环境变量
if [ -z "$DB_DSN" ]; then
    echo "Error: DB_DSN environment variable is not set"
    echo "Please set DB_DSN in .env file or as an environment variable"
    echo "Expected .env file location: $ENV_FILE"
    exit 1
fi

# 设置 PYTHONPATH 以包含 src 目录
export PYTHONPATH="${PYTHONPATH}:$PROJECT_ROOT/src"

# 运行数据库迁移
echo "Running database migrations..."
python -m alembic upgrade head || {
    echo "Warning: Failed to run migrations, continuing..."
}

# 启动服务
echo "Starting service..."
exec python -m uvicorn api.main:app --host 0.0.0.0 --port 8001
