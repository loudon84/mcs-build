# MCS Platform 代码目录结构

本文档基于 `mcs-platform/` 目录的实际代码结构生成，参考 `architecture.md` 系统架构图。

```
mcs-platform/
├── README.md                          # 项目说明
├── pyproject.toml                     # 根项目配置
├── docker-compose.yaml                # Docker Compose 配置
│
├── libs/                              # 共享库
│   └── contracts/                     # 数据契约（Pydantic 模型）
│       ├── pyproject.toml
│       ├── src/
│       │   ├── __init__.py
│       │   ├── common.py              # 通用模型
│       │   ├── email_event.py         # 邮件事件模型
│       │   ├── masterdata.py          # 主数据模型
│       │   ├── orchestrator.py       # 编排器模型
│       │   ├── results.py             # 结果模型
│       │   └── mcs_contracts.py       # 主契约模块
│       └── tests/
│           └── test_schema_examples.py
│
├── orchestrator/                      # 统一编排服务（单节点部署）
│   │                                  # 合并了 gateway、masterdata、listener 功能
│   ├── pyproject.toml
│   ├── alembic.ini                    # Alembic 迁移配置
│   ├── .env                           # 环境变量配置
│   ├── README.md
│   ├── docker/
│   │   └── Dockerfile
│   ├── docs/
│   │   └── architecture.md            # 架构文档
│   ├── scripts/
│   │   └── migrate.ps1                # 数据库迁移脚本
│   ├── src/
│   │   ├── settings.py                # 配置管理（支持分库）
│   │   ├── errors.py                  # 错误定义
│   │   │
│   │   ├── api/                       # FastAPI API 层
│   │   │   ├── __init__.py
│   │   │   ├── main.py                # FastAPI 应用入口（lifespan 管理）
│   │   │   ├── deps.py                # 依赖注入（多数据库 Session、Services）
│   │   │   ├── middleware.py          # 中间件（请求ID、日志、异常处理）
│   │   │   ├── routes.py              # 旧路由（向后兼容）
│   │   │   ├── schemas.py             # API 请求/响应模式
│   │   │   └── routes/                # 按域拆分的路由
│   │   │       ├── __init__.py
│   │   │       ├── orchestration.py   # 编排路由（/v1/orchestrations/*）
│   │   │       ├── masterdata.py      # 主数据路由（/v1/masterdata/*）
│   │   │       ├── gateway.py         # 网关路由（/v1/orders/*）
│   │   │       └── listener.py        # 监听路由（/v1/listener/*）
│   │   │
│   │   ├── gateway/                   # Gateway 模块（ERP 集成）
│   │   │   ├── __init__.py
│   │   │   └── erp_client.py          # ERP 客户端
│   │   │
│   │   ├── masterdata/                # Masterdata 模块（主数据管理）
│   │   │   ├── __init__.py
│   │   │   ├── db/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── engine.py          # 主数据数据库引擎
│   │   │   │   └── models.py          # SQLAlchemy 模型（Customer, Contact, Company, Product, MasterDataVersion）
│   │   │   ├── cache/                 # 缓存层
│   │   │   │   ├── __init__.py
│   │   │   │   ├── memory_cache.py    # 内存缓存
│   │   │   │   └── redis_cache.py     # Redis 缓存
│   │   │   └── repo.py                # 主数据仓库（MasterDataRepo）
│   │   │
│   │   ├── listener/                  # Listener 模块（消息监听）
│   │   │   ├── __init__.py
│   │   │   ├── db/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── engine.py          # 监听器数据库引擎
│   │   │   │   └── models.py          # SQLAlchemy 模型（MessageRecord）
│   │   │   ├── clients/               # 第三方 API 客户端
│   │   │   │   ├── __init__.py
│   │   │   │   ├── exceptions.py      # 客户端异常类
│   │   │   │   └── alimail_client.py   # 阿里邮箱 REST API 客户端（OAuth + API 封装）
│   │   │   ├── listeners/             # 监听器实现
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py            # 基础监听器接口
│   │   │   │   ├── email.py           # 邮件监听器（IMAP）
│   │   │   │   ├── alimail_listener.py # 阿里邮箱监听器（REST API）
│   │   │   │   └── wechat.py          # 企业微信监听器
│   │   │   ├── processors/            # 消息处理器
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py            # 基础处理器接口
│   │   │   │   ├── email.py           # 邮件处理器
│   │   │   │   └── wechat.py          # 企业微信处理器
│   │   │   ├── repo.py                # 监听器仓库（ListenerRepo）
│   │   │   └── scheduler.py           # 统一调度器（UnifiedScheduler）
│   │   │
│   │   ├── services/                  # 服务层（跨模块通信）
│   │   │   ├── __init__.py
│   │   │   ├── gateway_service.py     # Gateway 服务（封装 ERP 客户端）
│   │   │   ├── masterdata_service.py   # Masterdata 服务（封装主数据仓库和缓存）
│   │   │   ├── listener_service.py    # Listener 服务（封装调度器和监听器）
│   │   │   └── orchestration_service.py  # Orchestration 服务（封装编排逻辑）
│   │   │
│   │   ├── db/                        # 编排数据库层（orchestration DB）
│   │   │   ├── __init__.py
│   │   │   ├── engine.py              # 编排数据库引擎
│   │   │   ├── models.py              # SQLAlchemy 模型（编排运行、幂等性、审计）
│   │   │   ├── repo.py                # 编排仓库（OrchestratorRepo）
│   │   │   ├── checkpoint/            # LangGraph 状态持久化
│   │   │   │   ├── __init__.py
│   │   │   │   └── postgres_checkpoint.py  # PostgreSQL Checkpoint
│   │   │   └── migrations/            # Alembic 迁移脚本
│   │   │       ├── env.py
│   │   │       ├── script.py.mako
│   │   │       └── versions/
│   │   │           └── 0001_init.py
│   │   │
│   │   ├── graphs/                     # LangGraph 图定义
│   │   │   ├── __init__.py
│   │   │   ├── registry.py            # 图注册表
│   │   │   └── sales_email/           # 销售邮件编排图
│   │   │       ├── __init__.py
│   │   │       ├── graph.py            # 图定义（节点、边、条件路由）
│   │   │       ├── state.py            # 状态定义（SalesEmailState）
│   │   │       ├── resume.py          # 恢复逻辑
│   │   │       └── nodes/              # 节点实现
│   │   │           ├── __init__.py
│   │   │           ├── check_idempotency.py      # 幂等性检查
│   │   │           ├── load_masterdata.py         # 加载主数据（使用 MasterDataService）
│   │   │           ├── match_contact.py           # 匹配联系人
│   │   │           ├── match_customer.py          # 匹配客户
│   │   │           ├── detect_contract_signal.py  # 检测合同信号
│   │   │           ├── upload_pdf.py              # 上传PDF
│   │   │           ├── call_dify_contract.py      # 调用 Dify 合同解析
│   │   │           ├── generate_candidates.py     # 生成候选订单
│   │   │           ├── call_dify_order_payload.py # 调用 Dify 订单载荷
│   │   │           ├── call_gateway.py            # 调用 ERP 网关（使用 GatewayService）
│   │   │           ├── notify_sales.py            # 通知销售
│   │   │           ├── persist_audit.py          # 持久化审计
│   │   │           └── finalize.py                # 完成节点
│   │   │
│   │   ├── tools/                      # 工具层（可复用）
│   │   │   ├── __init__.py
│   │   │   ├── dify_client.py         # Dify 客户端
│   │   │   ├── file_server.py         # 文件服务器客户端
│   │   │   ├── masterdata_client.py   # 主数据服务客户端（已废弃，使用 MasterDataService）
│   │   │   ├── similarity.py          # 相似度计算
│   │   │   └── mailer.py              # 邮件发送
│   │   │
│   │   └── observability/             # 可观测性
│   │       ├── __init__.py
│   │       ├── logging.py             # 日志配置
│   │       ├── metrics.py             # 指标收集
│   │       ├── monitoring.py          # 监控
│   │       ├── langsmith.py           # LangSmith 追踪
│   │       ├── redaction.py           # 数据脱敏
│   │       └── retry.py               # 重试策略
│   │
│   └── tests/                         # 测试
│       ├── test_checkpoint.py
│       ├── test_graph_happy_path.py
│       ├── test_graph_fail_paths.py
│       ├── test_idempotency.py
│       ├── test_manual_review_flow.py
│       └── test_retry.py
│
├── gateway/                           # 网关层
│   ├── README.md
│   └── nestjs-api/                    # NestJS 统一网关（权限/路由/鉴权）
│       ├── package.json
│       ├── nest-cli.json
│       ├── tsconfig.json
│       ├── .gitignore
│       ├── README.md
│       ├── src/
│       │   ├── main.ts                # NestJS 应用入口
│       │   ├── app.module.ts          # 根模块
│       │   ├── config/                # 配置管理
│       │   │   ├── config.module.ts
│       │   │   ├── config.service.ts
│       │   │   └── mcs-policy.yaml    # 权限策略配置
│       │   ├── auth/                  # 认证授权
│       │   │   ├── auth.module.ts
│       │   │   ├── auth.guard.ts      # 认证守卫
│       │   │   ├── jwt.strategy.ts    # JWT 策略
│       │   │   └── auth.types.ts
│       │   ├── policy/                # 权限策略引擎
│       │   │   ├── policy.module.ts
│       │   │   ├── policy.service.ts  # 策略服务
│       │   │   ├── policy.guard.ts    # 策略守卫
│       │   │   ├── policy.loader.ts   # 策略加载器
│       │   │   ├── policy.types.ts
│       │   │   └── policy.errors.ts
│       │   ├── proxy/                 # 代理服务
│       │   │   ├── proxy.module.ts
│       │   │   ├── proxy.service.ts   # 代理到后端服务
│       │   │   └── proxy.types.ts
│       │   ├── ratelimit/             # 限流
│       │   │   ├── ratelimit.module.ts
│       │   │   ├── ratelimit.service.ts
│       │   │   ├── ratelimit.guard.ts
│       │   │   └── ratelimit.types.ts
│       │   ├── modules/               # 业务模块
│       │   │   ├── health/            # 健康检查
│       │   │   │   ├── health.module.ts
│       │   │   │   └── health.controller.ts
│       │   │   ├── orchestrations/    # 编排服务代理
│       │   │   │   ├── orchestrations.module.ts
│       │   │   │   └── orchestrations.controller.ts
│       │   │   └── platform/          # 平台管理
│       │   │       ├── platform.module.ts
│       │   │       └── platform.controller.ts
│       │   ├── common/                # 通用功能
│       │   │   ├── constants.ts
│       │   │   ├── errors.ts          # 错误定义
│       │   │   ├── logger.ts          # 日志
│       │   │   ├── types.ts
│       │   │   ├── filters/           # 异常过滤器
│       │   │   │   ├── http-exception.filter.ts
│       │   │   │   └── upstream-exception.filter.ts
│       │   │   ├── interceptors/      # 拦截器
│       │   │   │   ├── logging.interceptor.ts
│       │   │   │   └── mcs-context.interceptor.ts
│       │   │   ├── middleware/        # 中间件
│       │   │   │   └── request-id.middleware.ts
│       │   │   └── utils/             # 工具函数
│       │   │       ├── headers.ts
│       │   │       └── request-id.ts
│       │   └── types/
│       │       └── express.d.ts       # Express 类型扩展
│       └── test/                      # 测试
│           ├── jest-e2e.json
│           ├── e2e.spec.ts
│           ├── auth.guard.spec.ts
│           ├── policy.service.spec.ts
│           ├── proxy.service.spec.ts
│           └── ratelimit.guard.spec.ts
│
├── infra/                             # 基础设施配置
│   └── k8s/                           # Kubernetes 部署
│       ├── namespace.yaml             # 命名空间
│       ├── configmap.yaml             # 配置映射
│       ├── deployment.yaml            # 部署清单
│       └── monitoring.yaml           # 监控配置
│
└── docs/                              # 项目文档
    ├── api.md                         # API 文档
    ├── api_examples.md                # API 示例
    ├── runbook.md                     # 运维手册
    ├── test_report.md                 # 测试报告
    └── email/                         # 邮件相关文档
        ├── 01_oauth_authorization.md  # OAuth 授权与 Token 获取
        ├── 02_list_folders_and_messages.md  # 获取邮箱文件夹列表和邮件列表
        ├── 03_get_message_and_attachments.md  # 获取邮件内容和附件
        ├── 04_create_and_send_message.md  # 创建邮件、上传附件和发送邮件
        ├── email_diff.md              # 阿里邮箱接口与实现差异分析
        └── mcs_listener_deployment_analysis.md  # 监听器部署分析
```

## 架构说明

### 统一编排服务（orchestrator/）

**单节点部署架构**：所有功能模块已合并到统一的编排服务中，支持模块化设计和分库部署。

#### 模块层（gateway/、masterdata/、listener/）

- **gateway/**: ERP 集成模块，提供 ERP 客户端封装
- **masterdata/**: 主数据管理模块，提供客户、联系人、产品等主数据的 CRUD 和缓存
- **listener/**: 消息监听模块，支持邮件（IMAP/阿里邮箱 REST API）和企业微信等消息源的监听和处理

**模块设计原则**：
- 模块间互不直接 import，通过服务层通信
- 每个模块使用独立的数据库（分库支持）
- 模块职责清晰，便于维护和扩展
- 模块位于 `src/` 目录下，与 `services/`、`api/` 等目录平级

#### 服务层（services/）

- **gateway_service.py**: Gateway 服务，封装 ERP 客户端调用
- **masterdata_service.py**: Masterdata 服务，封装主数据仓库和缓存逻辑
- **listener_service.py**: Listener 服务，封装调度器和监听器，支持进程内触发编排
- **orchestration_service.py**: Orchestration 服务，封装编排逻辑（run_sales_email、replay_sales_email、submit_manual_review）

**服务层职责**：
- 跨模块通信的唯一入口
- 统一依赖注入和生命周期管理
- 封装业务逻辑，提供统一接口

#### API 路由层（api/routes/）

- **orchestration.py**: `/v1/orchestrations/*` - 编排相关 API
- **masterdata.py**: `/v1/masterdata/*` - 主数据管理 API
- **gateway.py**: `/v1/orders/*` - ERP 订单 API
- **listener.py**: `/v1/listener/*` - 监听器管理 API

**路由设计**：
- 每个功能域有独立的路由前缀
- 路由仅依赖服务层，不直接访问模块
- 支持独立部署和扩展

#### 数据库分库支持

- **orchestration_db_dsn**: 编排数据库（编排运行、幂等性、审计记录）
- **masterdata_db_dsn**: 主数据数据库（客户、联系人、产品、版本）
- **listener_db_dsn**: 监听器数据库（消息记录）

### 网关层（gateway/）

- **nestjs-api**: NestJS 统一网关，提供：
  - 统一鉴权（JWT）
  - 权限策略引擎（基于 YAML 配置）
  - 请求代理到后端服务
  - 限流和审计

### 共享库（libs/）

- **contracts**: Pydantic 数据契约，定义服务间通信的数据模型

### 基础设施（infra/）

- **k8s**: Kubernetes 部署配置，包括命名空间、部署、配置映射和监控

## 扩展点

以下为代码级扩展时需触及的路径与契约。Listener/工具「插件化」为后续设计方向，当前仍为代码级扩展。

| 扩展点 | 涉及路径/文件 | 契约与说明 |
|--------|----------------|------------|
| 新增编排图 | `orchestrator/src/graphs/registry.py`、`graphs/<name>/`（graph.py、state.py、nodes/） | 在 registry 注册；state 与 contracts 对齐；路由挂载到 `/v1/orchestrations/<graph>/run` 等 |
| 新增节点 | `graphs/<graph>/nodes/<node>.py` | 命名 `node_<action>_<object>`；入出使用 contracts 的 Result 或 state；只通过 Result/OrchestratorError 与外部通信 |
| 新增 Listener | `listener/listeners/`、`listener/processors/`、`listener/scheduler.py`（注册） | 实现 base 接口；processor 产出契约规定的入参（如 EmailEvent）；配置化启用 |
| 新增工具 | `tools/<name>.py` | 返回 contracts 的 Result 或抛出 OrchestratorError；在节点中注入使用 |
| 新增 API 路由 | `api/routes/<domain>.py`、`main.py` include_router | 前缀 `/v1/<domain>`；在 [orchestration-protocol.md](orchestration-protocol.md) 端点清单中登记 |

**稳定接口**：对外暴露的 API 路径与请求/响应模型（见 [orchestration-protocol.md](orchestration-protocol.md)）、contracts 的 Result 与稳定字段。**内部实现**：节点实现、listener/processor 具体类、工具函数内部逻辑；扩展时尽量不破坏稳定接口。

## 技术栈

- **Python 3.12**: 所有 Python 服务
- **FastAPI**: Python 服务 API 框架
- **LangGraph + LangServe**: 编排服务核心
- **SQLAlchemy + Alembic**: ORM 和数据库迁移
- **NestJS**: 统一网关
- **PostgreSQL**: 主数据库（支持分库）
- **Redis**: 缓存和状态存储
- **Kubernetes**: 容器编排

## 架构优势

1. **单节点部署**：所有功能统一在一个服务中，简化部署和运维
2. **模块化设计**：模块职责清晰，互不依赖，便于维护和扩展
3. **分库支持**：不同模块使用独立数据库，支持数据隔离和扩展
4. **服务层解耦**：通过服务层实现跨模块通信，避免直接依赖
5. **独立 API 路由**：每个功能域有独立的路由前缀，便于 API 管理和版本控制
6. **进程内调用**：模块间通信无需 HTTP，提高性能和可靠性

## 文档导航

| 文档 | 说明 |
|------|------|
| [architecture.md](architecture.md) | 顶层结构、系统生命周期、高风险修改、不变式 |
| [orchestration-protocol.md](orchestration-protocol.md) | 编排协议与 API 端点清单（请求/响应/错误码/幂等） |
| [improve.md](improve.md) | 架构分析与改进要点（对照 OpenClaw） |
| [contracts-analysis.md](contracts-analysis.md) | libs/contracts 架构作用分析 |
| [sitemap.md](sitemap.md) | 本页：代码目录结构、架构说明、扩展点 |
| [nestjs-api.md](nestjs-api.md) | NestJS 网关 API |
| [api.md](../mcs-platform/docs/api.md) | API 文档 |
| [runbook.md](../mcs-platform/docs/runbook.md) | 运维手册 |
