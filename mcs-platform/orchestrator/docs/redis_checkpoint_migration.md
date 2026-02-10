# PostgreSQL → Redis Checkpoint 迁移指南

## 一、迁移概述

### 1.1 为什么迁移到 Redis？

**优势**:
- ✅ **性能更好**: 内存存储，读写速度更快
- ✅ **Windows 兼容性**: 不依赖 `psycopg`，避免 `ProactorEventLoop` 问题
- ✅ **分布式支持**: Redis 天然支持分布式部署
- ✅ **简化配置**: 无需数据库连接池管理
- ✅ **自动过期**: Redis TTL 自动清理旧数据

**劣势**:
- ⚠️ **内存限制**: 数据存储在内存中，需要足够的 Redis 内存
- ⚠️ **持久化**: 需要配置 Redis 持久化策略（RDB/AOF）
- ⚠️ **Redis 模块**: 需要 RedisJSON 和 RediSearch 模块（Redis 8.0+ 内置）

### 1.2 Windows 兼容性

**好消息**: Redis checkpoint **不会**出现 `SelectorEventLoop` 问题！

**原因**:
- `redis.asyncio` 使用标准的 `asyncio` API，不依赖特定的事件循环类型
- `redis.asyncio` 在 Windows 上使用 `ProactorEventLoop` 和 `SelectorEventLoop` 都可以正常工作
- 不需要像 `psycopg` 那样强制使用 `SelectorEventLoop`

**结论**: 迁移到 Redis checkpoint 后，可以**移除所有事件循环策略设置代码**！

## 二、需要修改的文件

### 2.1 核心文件修改清单

| 文件路径 | 修改类型 | 说明 |
|---------|---------|------|
| `src/db/checkpoint/redis_checkpoint.py` | ✅ **新建** | Redis checkpoint store 实现 |
| `src/db/checkpoint/postgres_checkpoint.py` | ⚠️ **保留或删除** | 可选：保留作为备份 |
| `src/services/orchestration_service.py` | 🔄 **修改** | 替换 `PostgresCheckpointStore` 为 `RedisCheckpointStore` |
| `src/api/routes.py` | 🔄 **修改** | 替换 `PostgresCheckpointStore` 为 `RedisCheckpointStore` |
| `src/graphs/sales_email/graph.py` | 🔄 **修改** | 替换类型注解和导入 |
| `pyproject.toml` | 🔄 **修改** | 添加 `langgraph-checkpoint-redis`，可选移除 `langgraph-checkpoint-postgres` |
| `src/main.py` | 🔄 **修改** | 可选：移除事件循环策略设置（不再需要） |
| `src/api/main.py` | 🔄 **修改** | 可选：移除事件循环策略设置（不再需要） |
| `src/services/orchestration_service.py` | 🔄 **修改** | 移除 `ensure_selector_event_loop()` 调用 |
| `.env` | 🔄 **修改** | 确保 `REDIS_URL` 配置正确 |

### 2.2 依赖配置修改

**pyproject.toml**:
```toml
dependencies = [
    "langgraph>=0.2.0",
    "langgraph-checkpoint-redis>=0.3.0",  # 新增
    # "langgraph-checkpoint-postgres>=3.0.0",  # 可选：移除
    # "psycopg[binary]>=3.1.0",  # 可选：如果不再使用 PostgreSQL checkpoint，可以移除
    "redis>=5.0.0",  # 已存在
    # ... 其他依赖
]
```

## 三、代码修改步骤

### 步骤 1: 安装依赖

```bash
conda activate mcs-platform
pip install langgraph-checkpoint-redis>=0.3.0
```

### 步骤 2: 创建 Redis checkpoint store

已创建: `src/db/checkpoint/redis_checkpoint.py`

### 步骤 3: 修改 `orchestration_service.py`

**修改前**:
```python
from db.checkpoint.postgres_checkpoint import PostgresCheckpointStore

# ...
checkpoint_store = PostgresCheckpointStore(self.settings)
await checkpoint_store.initialize()
```

**修改后**:
```python
from db.checkpoint.redis_checkpoint import RedisCheckpointStore

# ...
checkpoint_store = RedisCheckpointStore(self.settings)
await checkpoint_store.initialize()
```

### 步骤 4: 修改 `api/routes.py`

**修改前**:
```python
from db.checkpoint.postgres_checkpoint import PostgresCheckpointStore

# ...
checkpoint_store = PostgresCheckpointStore(settings)
await checkpoint_store.initialize()
```

**修改后**:
```python
from db.checkpoint.redis_checkpoint import RedisCheckpointStore

# ...
checkpoint_store = RedisCheckpointStore(settings)
await checkpoint_store.initialize()
```

### 步骤 5: 修改 `graphs/sales_email/graph.py`

**修改前**:
```python
from db.checkpoint.postgres_checkpoint import PostgresCheckpointStore

def build_sales_email_graph(
    # ...
    checkpoint_store: PostgresCheckpointStore,
    # ...
):
```

**修改后**:
```python
from db.checkpoint.redis_checkpoint import RedisCheckpointStore

def build_sales_email_graph(
    # ...
    checkpoint_store: RedisCheckpointStore,
    # ...
):
```

### 步骤 6: 移除事件循环策略设置（可选）

**可以移除的文件**:
- `src/main.py`: 移除 `WindowsSelectorEventLoopPolicy` 设置
- `src/api/main.py`: 移除 `WindowsSelectorEventLoopPolicy` 设置
- `src/services/orchestration_service.py`: 移除 `ensure_selector_event_loop()` 函数和调用
- `src/db/checkpoint/postgres_checkpoint.py`: 如果删除，移除事件循环检查代码

**注意**: 如果项目中还有其他地方使用 `psycopg`（如数据库连接），**不要移除**事件循环策略设置。

### 步骤 7: 更新环境变量

确保 `.env` 文件中有正确的 Redis 配置：

```env
REDIS_URL=redis://localhost:6379/0
```

如果 Redis 需要密码：
```env
REDIS_URL=redis://:password@localhost:6379/0
```

## 四、Windows 下的潜在问题

### 4.1 ✅ 不会出现的问题

1. **SelectorEventLoop 问题**: Redis checkpoint **不会**出现此问题
   - `redis.asyncio` 兼容所有事件循环类型
   - 不需要特殊的事件循环策略设置

2. **连接池超时问题**: Redis checkpoint **不会**出现此问题
   - Redis 连接管理更简单
   - 不需要复杂的连接池配置

### 4.2 ⚠️ 可能的问题

1. **Redis 服务器未启动**
   - **错误**: `ConnectionError` 或 `ConnectionRefusedError`
   - **解决**: 确保 Redis 服务器正在运行

2. **Redis 模块缺失**（Redis < 8.0）
   - **错误**: `ModuleNotFoundError` 或 Redis 命令失败
   - **解决**: 安装 RedisJSON 和 RediSearch 模块，或升级到 Redis 8.0+

3. **Redis 内存不足**
   - **错误**: `OOM command not allowed` 或性能下降
   - **解决**: 增加 Redis 内存限制或配置 TTL

4. **网络连接问题**
   - **错误**: `TimeoutError` 或连接超时
   - **解决**: 检查网络连接和防火墙设置

### 4.3 Redis 版本要求

**推荐**: Redis 8.0+（内置 RedisJSON 和 RediSearch）

**最低**: Redis 6.0+（需要安装 RedisJSON 和 RediSearch 模块）

**检查 Redis 版本**:
```bash
redis-cli INFO server | grep redis_version
```

**检查模块**:
```bash
redis-cli MODULE LIST
```

应该看到：
- `ReJSON`
- `search`

## 五、测试验证

### 5.1 基本功能测试

1. **连接测试**:
   ```python
   from db.checkpoint.redis_checkpoint import RedisCheckpointStore
   from settings import Settings
   
   settings = Settings.from_env()
   store = RedisCheckpointStore(settings)
   await store.initialize()
   # 应该成功连接 Redis
   ```

2. **Checkpoint 保存和恢复**:
   ```python
   saver = store.get_checkpoint_saver_sync()
   # 测试保存和恢复 checkpoint
   ```

3. **图执行测试**:
   - 运行完整的 sales email orchestration
   - 验证 checkpoint 是否正确保存
   - 验证断点续跑功能

### 5.2 Windows 兼容性测试

1. **事件循环测试**:
   - 在 Windows 上运行应用
   - 验证不需要 `SelectorEventLoop` 设置
   - 验证 `ProactorEventLoop` 可以正常工作

2. **性能测试**:
   - 对比 PostgreSQL 和 Redis checkpoint 的性能
   - 验证高并发场景下的表现

## 六、回滚方案

如果迁移后出现问题，可以快速回滚：

1. **恢复代码**: 使用 Git 回滚到之前的版本
2. **恢复依赖**: 重新安装 `langgraph-checkpoint-postgres`
3. **恢复配置**: 确保 PostgreSQL 数据库可用

## 七、性能对比

### 7.1 预期性能提升

- **写入速度**: Redis 比 PostgreSQL 快 10-100 倍（内存 vs 磁盘）
- **读取速度**: Redis 比 PostgreSQL 快 5-50 倍
- **延迟**: Redis 延迟通常 < 1ms，PostgreSQL 延迟通常 1-10ms

### 7.2 资源消耗

- **内存**: Redis 需要更多内存（所有数据在内存中）
- **CPU**: Redis CPU 消耗通常更低
- **网络**: Redis 网络流量可能更高（如果 Redis 在远程服务器）

## 八、总结

### 8.1 迁移优势

1. ✅ **解决 Windows 兼容性问题**: 不再需要 `SelectorEventLoop`
2. ✅ **性能提升**: 内存存储，读写速度更快
3. ✅ **简化配置**: 无需数据库连接池管理
4. ✅ **分布式支持**: Redis 天然支持分布式部署

### 8.2 注意事项

1. ⚠️ **Redis 版本**: 需要 Redis 8.0+ 或安装 RedisJSON/RediSearch 模块
2. ⚠️ **内存管理**: 需要足够的 Redis 内存和 TTL 配置
3. ⚠️ **持久化**: 需要配置 Redis 持久化策略

### 8.3 推荐操作

1. ✅ **立即迁移**: 如果遇到 Windows `SelectorEventLoop` 问题
2. ✅ **性能优先**: 如果需要更高的 checkpoint 性能
3. ⚠️ **谨慎迁移**: 如果 Redis 服务器不稳定或内存不足
