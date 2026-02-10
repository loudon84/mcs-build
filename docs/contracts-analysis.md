# mcs-platform/libs/contracts 架构作用分析

## 概述

`mcs-platform/libs/contracts` 是 MCS 平台的核心共享库，提供统一的数据契约（Data Contracts）定义。它作为整个微服务架构的**数据模型标准**和**服务间通信协议**，确保各服务之间的数据一致性和类型安全。

## 核心作用

### 1. **共享数据模型定义（Shared Data Models）**

提供全平台统一的数据结构定义，包括：

#### 1.1 领域模型（Domain Models）
- **EmailEvent** (`email_event.py`): 邮件事件模型，包含邮件元数据、附件等
- **EmailAttachment**: 邮件附件模型，包含文件信息、SHA256 哈希等
- **MasterData** (`masterdata.py`): 主数据容器
  - `Customer`: 客户模型
  - `Contact`: 联系人模型
  - `Company`: 公司模型
  - `Product`: 产品模型

#### 1.2 操作结果模型（Result Models）
所有工具和节点操作的统一返回格式（`results.py`）：
- `ContactMatchResult`: 联系人匹配结果
- `CustomerMatchResult`: 客户匹配结果
- `ContractSignalResult`: 合同信号检测结果
- `FileUploadResult`: 文件上传结果
- `DifyContractResult`: Dify 合同识别结果
- `DifyOrderPayloadResult`: Dify 订单载荷生成结果
- `ERPCreateOrderResult`: ERP 订单创建结果

**设计模式**：所有 Result 模型都遵循统一结构：
```python
class XxxResult(BaseModel):
    ok: bool  # 操作是否成功（第一个字段）
    # 具体数据字段
    warnings: list[str]  # 警告信息
    errors: list[ErrorInfo]  # 错误信息
```

#### 1.3 编排模型（Orchestration Models）
- `OrchestratorRunResult`: 编排执行结果
- `ManualReviewCandidates`: 人工审核候选对象
- `ManualReviewDecision`: 人工审核决策
- `ManualReviewSubmitRequest/Response`: 人工审核提交请求/响应

#### 1.4 通用类型（Common Types）
- `StatusEnum`: 编排状态枚举（IGNORED, UNKNOWN_CONTACT, MANUAL_REVIEW, SUCCESS 等）
- `ErrorInfo`: 错误信息结构（code, reason, details）
- `now_iso()`: 时间工具函数

### 2. **服务间通信协议（Inter-Service Communication Protocol）**

作为微服务架构中的**契约层（Contract Layer）**，定义服务间 API 的数据格式：

#### 2.1 API 请求/响应模型
- **Listener Service → Orchestrator**: 使用 `EmailEvent` 传递邮件事件
- **Orchestrator → MasterData Service**: 使用 `MasterData` 模型
- **Orchestrator → Gateway Service**: 使用 `ERPCreateOrderResult` 返回订单创建结果
- **Manual Review API**: 使用 `ManualReviewSubmitRequest/Response` 进行交互

#### 2.2 LangGraph 状态定义基础
`SalesEmailState`（编排图状态）完全基于 contracts 模型构建：
```python
class SalesEmailState(BaseModel):
    email_event: EmailEvent  # 输入
    masterdata: Optional[MasterData]  # 主数据
    matched_contact: Optional[ContactMatchResult]  # 匹配结果
    contract_signals: Optional[ContractSignalResult]
    matched_customer: Optional[CustomerMatchResult]
    # ... 其他状态字段都使用 contracts 模型
```

### 3. **类型安全与验证（Type Safety & Validation）**

#### 3.1 Pydantic 验证
- **字段验证**: 自动验证数据类型、格式、范围
  - `EmailStr`: 邮箱格式验证
  - `ge=0.0, le=100.0`: 分数范围验证
  - `SHA256`: 64 位十六进制字符验证
- **业务规则验证**: 
  - 附件大小限制（50MB）
  - 邮箱地址规范化（小写、去空格）

#### 3.2 类型提示（Type Hints）
提供完整的类型提示，支持：
- IDE 自动补全
- 静态类型检查（mypy）
- 文档生成

### 4. **代码复用与一致性（Code Reusability & Consistency）**

#### 4.1 避免重复定义
- 各服务无需重复定义相同的数据模型
- 统一的字段命名规范（snake_case）
- 统一的错误处理格式

#### 4.2 版本管理
- 独立的版本号管理（当前 v0.1.0）
- 通过依赖管理控制模型变更影响范围

### 5. **架构边界定义（Architecture Boundaries）**

#### 5.1 服务边界
```
┌─────────────────────────────────────────┐
│         mcs-contracts (共享库)           │
│  ┌──────────┐  ┌──────────┐  ┌───────┐ │
│  │ EmailEvent│  │MasterData│  │Results│ │
│  └──────────┘  └──────────┘  └───────┘ │
└─────────────────────────────────────────┘
         ▲              ▲              ▲
         │              │              │
    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
    │Listener │    │Orchestr │    │Gateway  │
    │Service  │    │ator     │    │Service  │
    └─────────┘    └─────────┘    └─────────┘
```

#### 5.2 依赖关系
- **所有服务依赖 contracts**: 通过 `mcs-contracts` 包引入
- **Contracts 独立**: 不依赖任何业务服务，只依赖 Pydantic
- **向下兼容**: 模型变更需要考虑向后兼容性

## 使用场景

### 场景 1: 邮件监听服务 → 编排服务
```python
# listener_service.py
from mcs_contracts import EmailEvent

email_event = EmailEvent(
    message_id="...",
    from_email="customer@example.com",
    # ...
)
await orchestration_service.run_sales_email(email_event)
```

### 场景 2: LangGraph 节点返回结果
```python
# nodes/match_customer.py
from mcs_contracts import CustomerMatchResult, ErrorInfo

def node_match_customer(state: SalesEmailState) -> SalesEmailState:
    # ... 匹配逻辑
    result = CustomerMatchResult(
        ok=True,
        customer_id="C001",
        score=95.5,
        # ...
    )
    state.matched_customer = result
    return state
```

### 场景 3: API 响应序列化
```python
# api/routes.py
from mcs_contracts import OrchestratorRunResult

@router.post("/run")
async def run_sales_email(...) -> OrchestratorRunResult:
    result = await orchestration_service.run_sales_email(...)
    return result  # FastAPI 自动序列化为 JSON
```

## 技术实现

### 包结构
```
libs/contracts/
├── pyproject.toml          # 包配置，定义依赖（Pydantic）
├── src/
│   ├── __init__.py         # 统一导出接口
│   ├── mcs_contracts.py    # 包入口点（兼容性）
│   ├── common.py           # 通用类型和工具
│   ├── email_event.py      # 邮件事件模型
│   ├── masterdata.py       # 主数据模型
│   ├── results.py          # 结果模型
│   └── orchestrator.py     # 编排相关模型
└── tests/
    └── test_schema_examples.py
```

### 安装方式
```toml
# orchestrator/pyproject.toml
dependencies = [
    "mcs-contracts",  # 本地可编辑安装
]
```

### 导入方式
```python
# 统一从 mcs_contracts 导入
from mcs_contracts import (
    EmailEvent,
    MasterData,
    CustomerMatchResult,
    StatusEnum,
)
```

## 设计原则

### 1. **单一数据源（Single Source of Truth）**
- 每个数据模型只有一个定义位置
- 避免服务间数据不一致

### 2. **不可变性优先（Immutability First）**
- 使用 Pydantic BaseModel（默认不可变）
- 通过 `model_copy()` 进行状态更新

### 3. **向后兼容（Backward Compatibility）**
- 新增字段使用 `Optional` 或默认值
- 避免删除或重命名字段（除非大版本升级）

### 4. **明确的错误处理（Explicit Error Handling）**
- 所有 Result 模型包含 `ok: bool` 和 `errors: list[ErrorInfo]`
- 统一的错误码规范（UPPER_SNAKE_CASE）

## 在系统架构中的位置

```
┌─────────────────────────────────────────────────────────┐
│                    MCS Platform                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Listener   │  │ Orchestrator │  │   Gateway    │ │
│  │   Service    │  │   Service    │  │   Service    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                  │                  │         │
│         └──────────────────┼──────────────────┘         │
│                            │                            │
│                  ┌─────────▼─────────┐                  │
│                  │  mcs-contracts   │                  │
│                  │  (共享数据契约)   │                  │
│                  └───────────────────┘                  │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   MasterData │  │   Dify API   │  │   ERP API    │ │
│  │   Service    │  │              │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 优势总结

1. **类型安全**: 编译时和运行时类型检查
2. **一致性**: 统一的数据格式和命名规范
3. **可维护性**: 集中管理数据模型，易于更新和维护
4. **可测试性**: 模型可以独立测试和验证
5. **文档化**: Pydantic 自动生成 JSON Schema 和 OpenAPI 文档
6. **解耦**: 服务间通过契约通信，降低耦合度

## 注意事项

1. **版本管理**: 模型变更需要谨慎，考虑向后兼容
2. **循环依赖**: contracts 不应依赖业务服务
3. **性能**: Pydantic 验证有性能开销，但提供了安全保障
4. **序列化**: 确保模型可以正确序列化为 JSON（用于 API 和持久化）

## 未来扩展方向

1. **版本化**: 支持多版本模型共存（v1, v2）
2. **迁移工具**: 提供模型版本迁移工具
3. **文档生成**: 自动生成 API 文档和模型说明
4. **验证规则**: 扩展业务规则验证（如邮箱域名白名单）
5. **国际化**: 支持多语言错误消息
