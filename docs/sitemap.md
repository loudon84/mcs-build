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
│       │   └── mcs_contracts/
│       │       ├── __init__.py
│       │       ├── common.py          # 通用模型
│       │       ├── email_event.py     # 邮件事件模型
│       │       ├── masterdata.py      # 主数据模型
│       │       ├── orchestrator.py    # 编排器模型
│       │       └── results.py         # 结果模型
│       └── tests/
│           └── test_schema_examples.py
│
├── services/                          # Python 微服务
│   ├── mcs-masterdata/                # 主数据管理服务
│   │   ├── pyproject.toml
│   │   ├── alembic.ini                # Alembic 迁移配置
│   │   ├── docker/
│   │   │   └── Dockerfile
│   │   └── src/
│   │       └── mcs_masterdata/
│   │           ├── __init__.py
│   │           ├── settings.py        # 配置管理
│   │           ├── schemas.py         # API 模式定义
│   │           ├── errors.py          # 错误定义
│   │           ├── api/               # FastAPI 接口
│   │           │   ├── __init__.py
│   │           │   ├── main.py        # FastAPI 应用入口
│   │           │   ├── routes.py      # 路由定义
│   │           │   └── deps.py        # 依赖注入
│   │           ├── db/                # 数据库层
│   │           │   ├── __init__.py
│   │           │   ├── engine.py      # 数据库引擎
│   │           │   ├── models.py      # SQLAlchemy 模型
│   │           │   ├── repo.py        # 数据仓库模式
│   │           │   └── migrations/    # Alembic 迁移脚本
│   │           │       ├── env.py
│   │           │       ├── script.py.mako
│   │           │       └── versions/
│   │           │           └── 0001_init.py
│   │           └── cache/             # 缓存层
│   │               ├── __init__.py
│   │               ├── memory_cache.py # 内存缓存
│   │               └── redis_cache.py  # Redis 缓存
│   │
│   ├── mcs-listener/                  # 多通道监听服务（邮件/企业微信等）
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── docker/
│   │   │   └── Dockerfile
│   │   ├── tests/                     # 测试
│   │   │   ├── __init__.py
│   │   │   ├── test_clients/
│   │   │   │   ├── __init__.py
│   │   │   │   └── test_alimail_client.py  # 阿里邮箱客户端测试
│   │   │   └── test_listeners/
│   │   │       ├── __init__.py
│   │   │       └── test_alimail_listener.py  # 阿里邮箱监听器测试
│   │   └── src/
│   │       ├── mcs_email_listener/    # 邮件监听器（旧版/独立）
│   │       │   ├── __init__.py
│   │       │   ├── settings.py
│   │       │   ├── errors.py
│   │       │   ├── fetcher.py         # 邮件获取器
│   │       │   ├── scheduler.py       # 调度器
│   │       │   ├── api/
│   │       │   │   ├── main.py
│   │       │   │   └── routes.py
│   │       │   ├── db/
│   │       │   │   ├── models.py
│   │       │   │   └── repo.py
│   │       │   └── listeners/
│   │       │       ├── __init__.py
│   │       │       └── imap_listener.py
│   │       └── mcs_listener/          # 统一监听器（新版）
│   │           ├── __init__.py
│   │           ├── settings.py
│   │           ├── errors.py
│   │           ├── scheduler.py
│   │           ├── orchestrator_client.py  # 编排器客户端
│   │           ├── api/
│   │           │   ├── main.py
│   │           │   └── routes.py
│   │           ├── db/
│   │           │   ├── __init__.py
│   │           │   ├── engine.py
│   │           │   ├── models.py
│   │           │   └── repo.py
│   │           ├── clients/            # 第三方 API 客户端
│   │           │   ├── __init__.py
│   │           │   ├── exceptions.py   # 客户端异常类
│   │           │   └── alimail_client.py  # 阿里邮箱 REST API 客户端（OAuth + API 封装）
│   │           ├── listeners/          # 监听器实现
│   │           │   ├── __init__.py
│   │           │   ├── base.py        # 基础监听器
│   │           │   ├── email.py        # 邮件监听器（IMAP）
│   │           │   ├── alimail_listener.py  # 阿里邮箱监听器（REST API）
│   │           │   └── wechat.py       # 企业微信监听器
│   │           └── processors/        # 消息处理器
│   │               ├── __init__.py
│   │               ├── base.py         # 基础处理器
│   │               ├── email.py        # 邮件处理器
│   │               └── wechat.py       # 企业微信处理器
│   │
│   ├── mcs-gateway/                   # 外部系统集成网关（ERP 等）
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── docker/
│   │   │   └── Dockerfile
│   │   └── src/
│   │       ├── __init__.py
│   │       ├── settings.py
│   │       ├── errors.py
│   │       ├── api/
│   │       │   ├── main.py            # FastAPI 应用入口
│   │       │   └── routes.py          # 路由定义
│   │       └── clients/                # 外部系统客户端
│   │           ├── __init__.py
│   │           └── erp.py             # ERP 客户端
│   │
│   └── mcs-orchestrator/              # 编排服务（LangGraph + LangServe）
│       ├── pyproject.toml
│       ├── alembic.ini                # Alembic 迁移配置
│       ├── docker/
│       │   └── Dockerfile
│       ├── src/
│       │   └── mcs_orchestrator/
│       │       ├── __init__.py
│       │       ├── settings.py        # 配置管理
│       │       ├── errors.py          # 错误定义
│       │       ├── api/               # LangServe API（FastAPI）
│       │       │   ├── __init__.py
│       │       │   ├── main.py        # FastAPI 应用入口
│       │       │   ├── routes.py      # 路由定义（/invoke, /stream, /state）
│       │       │   ├── schemas.py     # API 请求/响应模式
│       │       │   ├── deps.py        # 依赖注入
│       │       │   └── middleware.py  # 中间件（请求ID、日志等）
│       │       ├── db/                # 数据库层
│       │       │   ├── __init__.py
│       │       │   ├── engine.py      # 数据库引擎
│       │       │   ├── models.py      # SQLAlchemy 模型（编排运行、幂等性、审计）
│       │       │   ├── repo.py        # 数据仓库模式
│       │       │   ├── checkpoint/    # LangGraph 状态持久化
│       │       │   │   ├── __init__.py
│       │       │   │   └── postgres_checkpoint.py  # PostgreSQL Checkpoint
│       │       │   └── migrations/    # Alembic 迁移脚本
│       │       │       ├── env.py
│       │       │       ├── script.py.mako
│       │       │       └── versions/
│       │       │           └── 0001_init.py
│       │       ├── graphs/            # LangGraph 图定义
│       │       │   ├── __init__.py
│       │       │   ├── registry.py    # 图注册表
│       │       │   └── sales_email/   # 销售邮件编排图
│       │       │       ├── __init__.py
│       │       │       ├── graph.py    # 图定义（节点、边、条件路由）
│       │       │       ├── state.py   # 状态定义（SalesEmailState）
│       │       │       ├── resume.py  # 恢复逻辑
│       │       │       └── nodes/      # 节点实现
│       │       │           ├── __init__.py
│       │       │           ├── check_idempotency.py      # 幂等性检查
│       │       │           ├── load_masterdata.py         # 加载主数据
│       │       │           ├── match_contact.py           # 匹配联系人
│       │       │           ├── match_customer.py          # 匹配客户
│       │       │           ├── detect_contract_signal.py  # 检测合同信号
│       │       │           ├── upload_pdf.py              # 上传PDF
│       │       │           ├── call_dify_contract.py      # 调用 Dify 合同解析
│       │       │           ├── generate_candidates.py     # 生成候选订单
│       │       │           ├── call_dify_order_payload.py # 调用 Dify 订单载荷
│       │       │           ├── call_gateway.py            # 调用 ERP 网关
│       │       │           ├── notify_sales.py            # 通知销售
│       │       │           ├── persist_audit.py          # 持久化审计
│       │       │           └── finalize.py                # 完成节点
│       │       ├── tools/              # 工具层（可复用）
│       │       │   ├── __init__.py
│       │       │   ├── dify_client.py         # Dify 客户端
│       │       │   ├── file_server.py         # 文件服务器客户端
│       │       │   ├── masterdata_client.py   # 主数据服务客户端
│       │       │   ├── similarity.py          # 相似度计算
│       │       │   └── mailer.py              # 邮件发送
│       │       ├── observability/     # 可观测性
│       │       │   ├── __init__.py
│       │       │   ├── logging.py     # 日志配置
│       │       │   ├── metrics.py     # 指标收集
│       │       │   ├── monitoring.py  # 监控
│       │       │   ├── langsmith.py   # LangSmith 追踪
│       │       │   ├── redaction.py   # 数据脱敏
│       │       │   └── retry.py       # 重试策略
│       │       └── templates/         # 模板（Jinja2）
│       │           ├── manual_review.j2    # 人工审核模板
│       │           ├── order_failed.j2     # 订单失败模板
│       │           └── order_success.j2    # 订单成功模板
│       └── tests/                     # 测试
│           ├── test_checkpoint.py
│           ├── test_graph_happy_path.py
│           ├── test_graph_fail_paths.py
│           ├── test_idempotency.py
│           ├── test_manual_review_flow.py
│           └── test_retry.py
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
│       └── monitoring.yaml            # 监控配置
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
        └── alimail_integration_plan.md  # 阿里邮箱 REST API 接入架构规划
```

## 架构说明

### 服务层（services/）

- **mcs-masterdata**: 主数据管理服务，提供客户、联系人、产品等主数据的 CRUD 和缓存
- **mcs-listener**: 多通道监听服务，支持邮件（IMAP/阿里邮箱 REST API）和企业微信等消息源的监听和处理
- **mcs-gateway**: 外部系统集成网关，封装 ERP 等外部系统的 API 调用
- **mcs-orchestrator**: 核心编排服务，基于 LangGraph 实现业务流程编排，通过 LangServe 暴露 API

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

## 技术栈

- **Python 3.12**: 所有 Python 服务
- **FastAPI**: Python 服务 API 框架
- **LangGraph + LangServe**: 编排服务核心
- **SQLAlchemy + Alembic**: ORM 和数据库迁移
- **NestJS**: 统一网关
- **PostgreSQL**: 主数据库
- **Redis**: 缓存和状态存储
- **Kubernetes**: 容器编排
