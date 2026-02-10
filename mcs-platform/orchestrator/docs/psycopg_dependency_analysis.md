# psycopg 依赖影响分析

## 一、psycopg 在代码中的使用位置

### 1.1 直接引用位置

**文件**: `src/db/checkpoint/postgres_checkpoint.py`

```python
# 第 9-10 行
from psycopg import AsyncConnection
from psycopg.rows import dict_row
```

**使用场景**:
- **第 35 行**: `self.conn: Optional[AsyncConnection] = None` - 类型注解
- **第 89 行**: `self.conn = await AsyncConnection.connect(...)` - 创建数据库连接
- **第 93 行**: `row_factory=dict_row` - 设置行工厂（必需）
- **第 126 行**: `await self.conn.close()` - 关闭连接

### 1.2 间接依赖位置

**文件**: `src/db/checkpoint/postgres_checkpoint.py`

```python
# 第 8 行
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# 第 110 行
self.checkpoint_saver = AsyncPostgresSaver(conn=self.conn)
```

**关键点**: `AsyncPostgresSaver` 的 `conn` 参数**必须**是 `psycopg.AsyncConnection` 类型。

## 二、LangGraph checkpoint postgres 包的依赖关系

### 2.1 langgraph-checkpoint-postgres 包要求

根据官方文档和源码分析：

1. **必需依赖**: `langgraph-checkpoint-postgres` 包**默认安装 `psycopg`**（Psycopg 3）
2. **连接类型**: `AsyncPostgresSaver` **仅支持 `psycopg.AsyncConnection`**，不支持其他驱动（如 `asyncpg`）
3. **必需参数**:
   - `autocommit=True`: 必需，用于 `.setup()` 方法正确提交表创建
   - `row_factory=dict_row`: 必需，因为 `AsyncPostgresSaver` 使用字典式访问（`row["column_name"]`）

### 2.2 AsyncPostgresSaver 的接口要求

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# AsyncPostgresSaver 的构造函数签名（简化）
class AsyncPostgresSaver:
    def __init__(self, conn: psycopg.AsyncConnection):
        # 内部使用 psycopg 特定的 API
        # 如: conn.cursor(), conn.execute(), 等
        pass
```

**关键限制**:
- `conn` 参数必须是 `psycopg.AsyncConnection` 类型
- 不能使用 `asyncpg.Connection` 或其他 PostgreSQL 驱动
- `langgraph-checkpoint-postgres` 包内部直接调用 `psycopg` 的 API

## 三、取消 psycopg 引用的影响分析

### 3.1 直接影响（无法工作）

#### ❌ 1. `PostgresCheckpointStore` 类无法实现

**影响文件**: `src/db/checkpoint/postgres_checkpoint.py`

**问题**:
- 无法创建 `AsyncConnection` 对象（第 89 行）
- 无法使用 `dict_row` 行工厂（第 93 行）
- `AsyncPostgresSaver` 无法初始化（第 110 行）

**错误示例**:
```python
# 如果移除 psycopg 导入
from psycopg import AsyncConnection  # ❌ ModuleNotFoundError
from psycopg.rows import dict_row   # ❌ ModuleNotFoundError

# 第 89 行会失败
self.conn = await AsyncConnection.connect(...)  # ❌ NameError: name 'AsyncConnection' is not defined
```

#### ❌ 2. LangGraph checkpoint 功能完全失效

**影响文件**:
- `src/graphs/sales_email/graph.py` (第 120-121 行)
- `src/services/orchestration_service.py` (第 84-85, 390-391 行)
- `src/api/routes.py` (第 89-90, 360-361 行)

**问题**:
- `build_sales_email_graph()` 无法编译图（第 121 行）
- `graph.compile(checkpointer=checkpoint_saver)` 需要有效的 checkpoint saver
- 所有使用 checkpoint 的功能都会失败

**错误示例**:
```python
# graph.py:120-121
checkpoint_saver = checkpoint_store.get_checkpoint_saver_sync()  # ❌ 返回 None 或抛出异常
return graph.compile(checkpointer=checkpoint_saver)  # ❌ 无法编译图
```

### 3.2 间接影响（功能缺失）

#### ⚠️ 1. 状态持久化功能失效

**影响功能**:
- ✅ **断点续跑（resume）**: 图执行中断后无法从上次状态恢复
- ✅ **人工审核恢复**: 人工审核通过后无法从指定节点恢复
- ✅ **状态查询**: 无法查询历史执行状态
- ✅ **状态更新**: 无法更新 checkpoint 状态

**影响代码**:
```python
# orchestration_service.py:376-410
# 人工审核恢复功能完全失效
current_state_dict = await graph.aget_state(config)  # ❌ 无法获取状态
await graph.aupdate_state(config, patched_state.model_dump())  # ❌ 无法更新状态
```

#### ⚠️ 2. 图执行无法持久化状态

**影响**:
- 每个节点执行后的状态快照无法保存
- 无法追踪图的执行历史
- 无法进行状态回滚或恢复

**影响代码**:
```python
# orchestration_service.py:106
result = await graph.ainvoke(initial_state.model_dump(), {"configurable": {"thread_id": run_id}})
# ❌ 如果没有 checkpoint，状态不会持久化，无法恢复
```

### 3.3 依赖链影响

#### 📦 依赖关系图

```
PostgresCheckpointStore
  ├─ psycopg.AsyncConnection (必需)
  ├─ psycopg.rows.dict_row (必需)
  └─ AsyncPostgresSaver (来自 langgraph-checkpoint-postgres)
      └─ 内部依赖 psycopg (必需)

build_sales_email_graph()
  └─ PostgresCheckpointStore (必需)
      └─ psycopg (必需)

orchestration_service.run_sales_email()
  └─ PostgresCheckpointStore (必需)
      └─ psycopg (必需)

orchestration_service.submit_manual_review()
  └─ PostgresCheckpointStore (必需)
      └─ psycopg (必需)
```

## 四、受影响文件清单

### 4.1 直接受影响文件

| 文件路径 | 影响类型 | 影响行数 | 说明 |
|---------|---------|---------|------|
| `src/db/checkpoint/postgres_checkpoint.py` | ❌ **完全无法工作** | 9-10, 35, 89, 93, 110, 126 | 核心实现文件，移除 psycopg 后完全失效 |
| `src/graphs/sales_email/graph.py` | ❌ **无法编译图** | 6, 34, 120-121 | 无法获取 checkpoint_saver，图无法编译 |
| `src/services/orchestration_service.py` | ❌ **核心功能失效** | 9, 84-85, 142, 390-391 | run_sales_email 和 submit_manual_review 无法工作 |
| `src/api/routes.py` | ❌ **API 端点失效** | 28, 89-90, 360-361 | API 端点无法处理请求 |

### 4.2 间接受影响文件

| 文件路径 | 影响类型 | 说明 |
|---------|---------|------|
| `src/api/routes/orchestration.py` | ⚠️ **功能受限** | 依赖 `OrchestrationService`，间接受影响 |
| `scripts/test_checkpoint_init.py` | ⚠️ **测试失效** | 测试脚本无法运行 |
| `pyproject.toml` | ⚠️ **依赖声明** | `psycopg[binary]>=3.1.0` 依赖声明 |

## 五、LangGraph 包的影响

### 5.1 langgraph-checkpoint-postgres 包

**包名**: `langgraph-checkpoint-postgres>=3.0.0`

**内部依赖**:
- **必需**: `psycopg` (Psycopg 3)
- **必需**: `langgraph` (核心包)

**关键类**: `AsyncPostgresSaver`

**限制**:
- ✅ **仅支持 psycopg**: `AsyncPostgresSaver` 只能使用 `psycopg.AsyncConnection`
- ❌ **不支持 asyncpg**: 不能使用 `asyncpg` 驱动
- ❌ **不支持其他驱动**: 不能使用其他 PostgreSQL 异步驱动

### 5.2 替代方案分析

#### ❌ 方案 1: 使用 asyncpg 驱动

**不可行原因**:
- `AsyncPostgresSaver` 内部直接调用 `psycopg` 的 API
- `asyncpg` 的 API 与 `psycopg` 不兼容
- `langgraph-checkpoint-postgres` 包没有提供 `asyncpg` 支持

#### ❌ 方案 2: 使用 SQLAlchemy 连接

**不可行原因**:
- `AsyncPostgresSaver` 需要 `psycopg.AsyncConnection` 对象
- SQLAlchemy 的连接对象类型不匹配
- 即使 SQLAlchemy 底层使用 `psycopg`，也无法直接传递

#### ⚠️ 方案 3: 实现自定义 CheckpointSaver

**可行性**: 理论上可行，但工作量巨大

**要求**:
- 实现 `BaseCheckpointSaver` 接口
- 实现所有 checkpoint 相关方法（`put`, `get`, `list`, `put_writes`, 等）
- 处理 checkpoint 表结构、版本管理、并发控制等
- 需要深入理解 LangGraph checkpoint 机制

**工作量**: 估计需要 2-4 周开发时间

#### ✅ 方案 4: 使用其他 checkpoint 后端

**可行方案**:
- **Redis checkpoint**: `langgraph-checkpoint-redis` 包
- **内存 checkpoint**: `MemorySaver`（仅用于开发/测试）
- **文件 checkpoint**: `FileSaver`（仅用于开发/测试）

**限制**:
- Redis checkpoint 需要 Redis 服务器
- 内存和文件 checkpoint 不支持分布式部署
- 需要修改代码以支持不同的 checkpoint 后端

## 六、取消 psycopg 的后果总结

### 6.1 无法工作的功能

1. ❌ **PostgreSQL checkpoint 存储**: 完全无法使用
2. ❌ **LangGraph 状态持久化**: 无法保存和恢复状态
3. ❌ **断点续跑功能**: 无法从中断处恢复执行
4. ❌ **人工审核恢复**: 无法从审核节点恢复执行
5. ❌ **状态查询和更新**: 无法查询和更新历史状态

### 6.2 需要修改的代码

如果取消 `psycopg`，需要：

1. **实现自定义 CheckpointSaver** (工作量: 2-4 周)
   - 实现 `BaseCheckpointSaver` 接口
   - 使用其他驱动（如 `asyncpg`）连接 PostgreSQL
   - 实现所有 checkpoint 方法

2. **修改所有使用 checkpoint 的代码** (工作量: 1-2 天)
   - `postgres_checkpoint.py`: 完全重写
   - `graph.py`: 修改 checkpoint 获取方式
   - `orchestration_service.py`: 修改 checkpoint 初始化
   - `api/routes.py`: 修改 checkpoint 使用方式

3. **更新依赖配置** (工作量: 几分钟)
   - `pyproject.toml`: 移除 `psycopg` 依赖
   - 添加新的 checkpoint 后端依赖（如 `langgraph-checkpoint-redis`）

### 6.3 推荐方案

**强烈建议保留 `psycopg` 依赖**，原因：

1. ✅ **LangGraph 官方支持**: `langgraph-checkpoint-postgres` 是官方推荐的 PostgreSQL checkpoint 实现
2. ✅ **功能完整**: 支持所有 checkpoint 功能（持久化、恢复、查询、更新）
3. ✅ **稳定可靠**: 经过充分测试，生产环境使用
4. ✅ **维护成本低**: 由 LangGraph 团队维护，自动获得更新和 bug 修复

**如果必须移除 `psycopg`**，推荐方案：

1. **使用 Redis checkpoint** (`langgraph-checkpoint-redis`)
   - 需要 Redis 服务器
   - 性能更好（内存存储）
   - 支持分布式部署

2. **实现自定义 CheckpointSaver**
   - 使用 `asyncpg` 或其他驱动
   - 需要大量开发工作
   - 需要自行维护和测试

## 七、结论

### 7.1 关键发现

1. **`psycopg` 是必需的**: `langgraph-checkpoint-postgres` 包**强制依赖** `psycopg`
2. **无法替代**: `AsyncPostgresSaver` **仅支持** `psycopg.AsyncConnection`
3. **影响范围广**: 移除 `psycopg` 会导致整个 checkpoint 功能失效

### 7.2 建议

**强烈建议保留 `psycopg` 依赖**，并解决 Windows 上的 `ProactorEventLoop` 问题（已通过设置事件循环策略解决）。

如果确实需要移除 `psycopg`（例如由于许可证问题），建议：

1. **评估替代方案**: 考虑使用 Redis checkpoint 或其他 checkpoint 后端
2. **评估工作量**: 实现自定义 CheckpointSaver 需要大量开发工作
3. **评估风险**: 自定义实现需要充分测试，可能存在未知问题

### 7.3 当前状态

当前代码已经通过以下方式解决了 `psycopg` 在 Windows 上的问题：

1. ✅ 在应用启动时设置 `WindowsSelectorEventLoopPolicy`
2. ✅ 在 Uvicorn 启动前创建 `SelectorEventLoop`
3. ✅ 在业务逻辑中检查事件循环类型
4. ✅ 在数据库连接时进行错误检测和处理

**建议**: 继续使用 `psycopg`，当前的事件循环修复方案已经解决了 Windows 兼容性问题。
