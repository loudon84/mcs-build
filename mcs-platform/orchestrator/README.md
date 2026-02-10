# MCS Orchestrator Service

MCS 平台编排服务，基于 LangGraph 和 LangServe 实现业务流程编排。

## 功能特性

- 基于 LangGraph 的工作流编排
- LangServe API 服务
- 数据库检查点和状态持久化
- 幂等性保证
- 审计日志记录

## 安装

```bash
# 使用 uv 安装
uv pip install -e .

# 或使用 conda 环境
conda activate mcs-platform
pip install -e .
```

## 配置

环境变量配置请参考 `.env.example` 文件。

## 数据库迁移

```bash
# 运行迁移
alembic upgrade head
```

## 运行服务

### 方式一：使用 main.py 入口（推荐）

```bash
# 从 orchestrator 目录运行
cd orchestrator
python src/main.py

# 或从项目根目录运行
python orchestrator/src/main.py

# 使用环境变量配置（可选）
HOST=0.0.0.0 PORT=18000 LOG_LEVEL=info python src/main.py
```

### 方式二：使用 uvicorn 直接运行

```bash
# 开发模式（自动重载）
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 18000

# 生产模式
uvicorn src.api.main:app --host 0.0.0.0 --port 18000
```

### 方式三：使用命令行入口点（安装后）

```bash
# 安装后可直接使用
mcs-orchestrator
```
