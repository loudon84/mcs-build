# MCS Listener Service

多通道通信监听服务，支持邮件、企业微信等多种通信工具。

## 架构设计

### 核心组件

1. **BaseListener** (`listeners/base.py`)
   - 通用监听器接口
   - 定义所有监听器必须实现的方法

2. **具体监听器实现**
   - `EmailListener`: 邮件监听（IMAP/Exchange/POP3）
   - `AlimailListener`: 阿里邮箱监听（REST API）
   - `WeChatListener`: 企业微信监听（框架已实现，待完善）

3. **消息处理器** (`processors/`)
   - `BaseProcessor`: 处理器基类
   - `EmailProcessor`: 邮件消息处理
   - `WeChatProcessor`: 企业微信消息处理

4. **统一调度器** (`scheduler.py`)
   - `UnifiedScheduler`: 支持多种监听器的统一调度
   - 自动轮询和消息处理

5. **数据库模型** (`db/models.py`)
   - `MessageRecord`: 统一消息记录（替代原来的 EmailRecord）
   - 支持多通道类型

## 配置

### 环境变量

```bash
# 启用的监听器（逗号分隔）
ENABLED_LISTENERS=email,wechat

# 邮件配置
EMAIL_PROVIDER=imap  # imap/exchange/pop3/alimail

# IMAP 配置
IMAP_HOST=imap.example.com
IMAP_PORT=993
IMAP_USER=sales@example.com
IMAP_PASS=password

# 阿里邮箱配置（当 EMAIL_PROVIDER=alimail 时使用）
ALIMAIL_CLIENT_ID=your_client_id
ALIMAIL_CLIENT_SECRET=your_client_secret
ALIMAIL_EMAIL_ACCOUNT=sales@example.com
ALIMAIL_FOLDER_ID=2  # 默认收件箱，可选值：1=发件箱, 2=收件箱, 3=垃圾箱, 5=草稿箱, 6=已删除
ALIMAIL_POLL_SIZE=100  # 每次轮询的邮件数量
ALIMAIL_API_BASE_URL=https://alimail-cn.aliyuncs.com  # 可选，默认值

# 企业微信配置
WECHAT_CORP_ID=your_corp_id
WECHAT_CORP_SECRET=your_corp_secret
WECHAT_AGENT_ID=your_agent_id
WECHAT_WEBHOOK_URL=https://your-webhook-url

# 轮询间隔（秒）
POLL_INTERVAL_SECONDS=60

# Orchestrator API
ORCHESTRATOR_API_URL=http://localhost:8000
ORCHESTRATOR_API_KEY=your_api_key

# 数据库
DB_DSN=postgresql://user:password@localhost:5432/mcs_listener
```

## API 端点

### Webhook 接收

#### 邮件 Webhook
```bash
POST /v1/webhook/email
```

#### 企业微信 Webhook
```bash
POST /v1/webhook/wechat
```

### 手动触发轮询
```bash
POST /v1/trigger/poll
```

### 服务状态
```bash
GET /v1/status
```

### 健康检查
```bash
GET /healthz
```

## 扩展新通道

### 1. 创建监听器

在 `listeners/` 目录下创建新的监听器类，继承 `BaseListener`：

```python
from listeners.base import BaseListener

class NewChannelListener(BaseListener):
    @property
    def channel_type(self) -> str:
        return "new_channel"
    
    async def connect(self) -> None:
        # 实现连接逻辑
        pass
    
    # ... 实现其他抽象方法
```

### 2. 创建处理器

在 `processors/` 目录下创建处理器，继承 `BaseProcessor`：

```python
from processors.base import BaseProcessor
from mcs_contracts import EmailEvent

class NewChannelProcessor(BaseProcessor):
    @property
    def channel_type(self) -> str:
        return "new_channel"
    
    def parse_to_event(self, message_data: dict) -> EmailEvent:
        # 将通道特定格式转换为 EmailEvent
        pass
```

### 3. 在调度器中注册

在 `scheduler.py` 的 `start()` 方法中添加新通道的初始化逻辑。

## 数据库迁移

从 `mcs-email-listener` 迁移到 `mcs-listener`：

1. 表名从 `email_records` 改为 `message_records`
2. 新增 `channel_type` 字段
3. 保留 `EmailRecord` 作为向后兼容别名

## 快速开始

### 1. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
# 编辑 .env 文件，填写实际配置值
```

### 2. 初始化数据库

```bash
# 创建数据库（如果尚未创建）
createdb mcs_listener

# 运行数据库迁移
alembic upgrade head
```

### 3. 启动服务

**方式一：使用启动脚本**
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

**方式二：直接运行**
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8001
```

**方式三：Docker 部署**
```bash
docker build -f docker/Dockerfile -t mcs-listener:latest .
docker run -d --name mcs-listener -p 8001:8001 --env-file .env mcs-listener:latest
```

### 4. 验证服务

```bash
# 健康检查
curl http://localhost:8001/healthz

# 服务状态
curl http://localhost:8001/v1/status
```

## 数据库迁移

### 创建新的迁移

```bash
# 自动生成迁移脚本（基于模型变更）
alembic revision --autogenerate -m "描述信息"

# 手动创建迁移脚本
alembic revision -m "描述信息"
```

### 应用迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade <revision>

# 降级一个版本
alembic downgrade -1

# 查看当前版本
alembic current

# 查看迁移历史
alembic history
```

## 开发状态

- ✅ 邮件监听（IMAP）已实现
- ✅ 邮件监听（阿里邮箱 REST API）已实现
- ⚠️ 企业微信监听框架已创建，待完善实现
- ⚠️ Exchange/POP3 支持待实现
- ✅ 统一调度器已实现
- ✅ 多通道消息处理已实现
- ✅ 数据库迁移配置已添加

## 阿里邮箱配置说明

### 前置条件

1. **版本要求**：需要使用阿里邮箱付费版本（免费版不支持 API 开放平台功能）
2. **管理员权限**：需要邮箱管理员权限来创建应用

### 获取应用凭证

1. 管理员登录**邮箱管理后台**
2. 进入**高级应用** → **API开放平台**
3. 点击**添加应用**
4. 勾选需要的接口权限（如邮件读取、发送等）
5. 保存应用配置
6. 再次编辑进入应用详情页面，获取：
   - **应用ID** (`client_id`)
   - **应用Secret** (`client_secret`)

### 配置示例

```bash
# 启用邮件监听
ENABLED_LISTENERS=email

# 选择阿里邮箱作为邮件提供商
EMAIL_PROVIDER=alimail

# 阿里邮箱 OAuth 配置
ALIMAIL_CLIENT_ID=your_client_id
ALIMAIL_CLIENT_SECRET=your_client_secret

# 邮箱账户配置
ALIMAIL_EMAIL_ACCOUNT=sales@example.com

# 文件夹配置（可选）
ALIMAIL_FOLDER_ID=2  # 默认收件箱

# 轮询配置（可选）
ALIMAIL_POLL_SIZE=100  # 每次轮询最多获取的邮件数量
```

### 常用文件夹 ID

| 文件夹名称 | 文件夹 ID |
|-----------|----------|
| 发件箱 | `1` |
| 收件箱 | `2` |
| 垃圾箱 | `3` |
| 草稿箱 | `5` |
| 已删除 | `6` |

### 功能特性

- ✅ OAuth 2.0 认证（自动 token 获取和刷新）
- ✅ 邮件列表获取（支持分页）
- ✅ 邮件详情获取
- ✅ 附件列表和下载（流式下载，支持大文件）
- ✅ 时区自动转换（UTC → 北京时间）
- ✅ 错误处理和自动重试

### 相关文档

详细的 API 接口文档请参考：
- [阿里邮箱 OAuth 授权文档](../docs/email/01_oauth_authorization.md)
- [获取邮箱文件夹和邮件列表](../docs/email/02_list_folders_and_messages.md)
- [获取邮件内容和附件](../docs/email/03_get_message_and_attachments.md)

