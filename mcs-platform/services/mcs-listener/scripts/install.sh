#!/bin/bash
# MCS Listener 独立部署安装脚本 (Bash)
# 用于在 conda mcs-platform 环境中安装 mcs-listener 及其依赖

set -e

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

echo "========================================"
echo "MCS Listener 独立部署安装脚本"
echo "========================================"
echo ""

# 检查 conda 环境
echo "[1/4] 检查 conda 环境..."
if ! conda env list | grep -q "mcs-platform"; then
    echo "错误: 未找到 conda 环境 'mcs-platform'"
    echo "请先创建并激活 conda 环境:"
    echo "  conda create -n mcs-platform python=3.12"
    echo "  conda activate mcs-platform"
    exit 1
fi
echo "✓ conda 环境 'mcs-platform' 已找到"

# 激活 conda 环境
echo ""
echo "[2/4] 激活 conda 环境..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate mcs-platform
if [ $? -ne 0 ]; then
    echo "错误: 无法激活 conda 环境 'mcs-platform'"
    exit 1
fi
echo "✓ conda 环境已激活"

# 检查项目路径
CONTRACTS_PATH="$PROJECT_ROOT/libs/contracts"
LISTENER_PATH="$PROJECT_ROOT/services/mcs-listener"

if [ ! -d "$CONTRACTS_PATH" ]; then
    echo "错误: 未找到 mcs-contracts 路径: $CONTRACTS_PATH"
    exit 1
fi

if [ ! -d "$LISTENER_PATH" ]; then
    echo "错误: 未找到 mcs-listener 路径: $LISTENER_PATH"
    exit 1
fi

# 安装 mcs-contracts
echo ""
echo "[3/4] 安装 mcs-contracts..."
cd "$CONTRACTS_PATH"
if pip install -e .; then
    echo "✓ mcs-contracts 安装成功"
else
    echo "错误: mcs-contracts 安装失败"
    exit 1
fi

# 安装 mcs-listener
echo ""
echo "[4/4] 安装 mcs-listener..."
cd "$LISTENER_PATH"
if pip install -e .; then
    echo "✓ mcs-listener 安装成功"
else
    echo "错误: mcs-listener 安装失败"
    exit 1
fi

# 验证安装
echo ""
echo "验证安装..."
if python -c "import mcs_contracts; from mcs_contracts import EmailEvent; print('OK')" 2>/dev/null; then
    echo "✓ mcs-contracts 导入测试通过"
else
    echo "警告: mcs-contracts 导入测试失败"
fi

echo ""
echo "========================================"
echo "安装完成！"
echo "========================================"
echo ""
echo "下一步:"
echo "1. 配置 .env 文件（如果尚未配置）"
echo "2. 运行数据库迁移: alembic upgrade head"
echo "3. 启动服务: python -m uvicorn api.main:app --host 0.0.0.0 --port 8001"
echo "   或使用启动脚本: ./scripts/start.sh"
echo ""
