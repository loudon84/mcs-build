# MCS Platform
Modeling Coordination System —— MCS
MCS Platform 是一个基于 LangGraph + LangServe 的 业务应用 -> 智能体-> 调度管理 系统平台。

## 项目结构

```
mcs-platform/
├── libs/
│   └── contracts/          # 共享数据契约（Pydantic 模型）
├── orchestrator/          # 统一编排服务（单节点部署）
│                           # 合并了 gateway、masterdata、listener 功能
│   ├── modules/           # 模块层（gateway, masterdata, listener）
│   ├── services/           # 服务层（跨模块通信）
│   ├── api/routes/         # API 路由层（按域拆分）
│   ├── db/                # 编排数据库层
│   ├── graphs/             # LangGraph 图定义
│   ├── tools/              # 工具层
│   └── observability/      # 可观测性
├── gateway/
│   └── nestjs-api/         # NestJS 网关
└── infra/
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

# 安装统一编排服务
cd ../../orchestrator
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

