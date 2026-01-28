# MCS Platform
Modeling Coordination System —— MCS
MCS Platform 是一个基于 LangGraph + LangServe 的 业务应用 -> 智能体-> 调度管理 系统平台。

## 项目结构

```
mcs-platform/
├── libs/
│   └── contracts/          # 共享数据契约（Pydantic 模型）
├── services/
│   ├── mcs-masterdata/     # 主数据管理服务
│   ├── mcs-listener/       # 多通道监听服务（邮件/企业微信等）
│   ├── mcs-gateway/        # 外部系统集成网关（ERP等）
│   └── mcs-orchestrator/   # 编排服务（LangGraph + LangServe）
├── gateway/
│   └── nestjs-api/         # NestJS 网关
└── infra/
    ├── docker/             # Docker 配置
    └── k8s/                # Kubernetes 配置
```

## 环境要求

- **Python**: 3.12
- **Conda 环境**: `mcs-platform`

## 快速开始

### 1. 创建 Conda 环境

```bash
conda create -n mcs-platform python=3.12
conda activate mcs-platform
```

### 2. 安装依赖

```bash
# 安装共享库
cd libs/contracts
pip install -e .

# 安装服务（按顺序）
cd ../../services/mcs-masterdata
pip install -e .

cd ../mcs-listener
pip install -e .

cd ../mcs-gateway
pip install -e .

cd ../mcs-orchestrator
pip install -e .
```

### 3. 配置环境变量

创建 `.env` 文件并配置必要的环境变量。

## 开发

- 使用 `ruff` 进行代码格式化和 linting
- 使用 `pytest` 进行测试
- 使用 `alembic` 进行数据库迁移

## 许可证

[待定]

