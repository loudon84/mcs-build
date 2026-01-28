# 创建邮件、上传附件和发送邮件

## 概述

本文档说明如何使用阿里邮箱开放平台 API 创建邮件草稿、上传附件，以及发送邮件。

## 前置条件

1. 已完成 OAuth 授权，获取到 `access_token`
2. 应用已获得相应的接口权限（邮件发送权限）

## 基本流程

发送带附件的邮件需要以下步骤：

1. **创建邮件草稿**：调用 `CreateMessage` 接口创建草稿，获取草稿 ID
2. **上传附件**（可选）：
   - 调用 `CreateAttachmentUploadSession` 创建上传会话，获取 `uploadUrl`
   - 从 `uploadUrl` 中提取 `session_id`
   - 调用文件流上传接口上传附件
3. **发送邮件**：调用 `SendMessage` 接口发送邮件

## 1. 创建邮件草稿

### 接口信息

- **接口名称**：CreateMessage（创建草稿）
- **接口地址**：`https://alimail-cn.aliyuncs.com/v2/users/{email_account}/messages`
- **请求方式**：`POST`
- **文档链接**：https://mailhelp.aliyun.com/openapi/index.html#/operations/alimailpb_alimail_mailagent_open_MailService_CreateMessage

### 请求参数

#### Path 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `email_account` | string | 是 | 用户邮箱地址 |

#### Body 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `message` | object | 是 | 邮件内容对象 |

### 邮件对象字段

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `internetMessageId` | string | 否 | 邮件唯一标识，建议使用 `email.utils.make_msgid()` 生成 |
| `subject` | string | 是 | 邮件主题 |
| `summary` | string | 否 | 邮件摘要 |
| `priority` | string | 否 | 优先级，可选值：`PRY_LOW`、`PRY_NORMAL`、`PRY_HIGH` |
| `isReadReceiptRequested` | boolean | 否 | 是否要求已读回执 |
| `from` | object | 是 | 发件人信息 |
| `toRecipients` | array | 否 | 收件人列表 |
| `ccRecipients` | array | 否 | 抄送人列表 |
| `bccRecipients` | array | 否 | 密送人列表 |
| `replyTo` | array | 否 | 回复地址列表 |
| `body` | object | 是 | 邮件正文 |
| `body.bodyText` | string | 否 | 纯文本正文 |
| `body.bodyHtml` | string | 否 | HTML格式正文 |
| `internetMessageHeaders` | object | 否 | 自定义邮件头 |
| `tags` | array | 否 | 邮件标签 |

### 请求头

```
Content-Type: application/json
Authorization: bearer {access_token}
```

### 请求示例

```python
import email
import requests

def create_draft(email_account, payload, access_token):
    """
    创建邮件草稿
    
    Args:
        email_account (str): 用户邮箱地址
        payload (dict): 邮件内容的JSON格式数据
        access_token (str): 访问凭证
    
    Returns:
        str: 创建的邮件草稿的ID
    """
    url = f"https://alimail-cn.aliyuncs.com/v2/users/{email_account}/messages"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'bearer {access_token}'
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    return response.json()["message"]["id"]

# 使用示例
email_account = "test@example.com"

payload = {
    "message": {
        "internetMessageId": email.utils.make_msgid(),
        "subject": "测试邮件主题",
        "summary": "这是邮件摘要",
        "priority": "PRY_NORMAL",
        "isReadReceiptRequested": True,
        "from": {
            "email": "test@example.com",
            "name": "发件人名称"
        },
        "toRecipients": [
            {
                "email": "recipient@example.com",
                "name": "收件人名称"
            }
        ],
        "ccRecipients": [
            {
                "email": "cc@example.com",
                "name": "抄送人名称"
            }
        ],
        "bccRecipients": [],
        "replyTo": [
            {
                "email": "reply@example.com",
                "name": "回复地址"
            }
        ],
        "body": {
            "bodyText": "这是邮件的纯文本内容",
            "bodyHtml": "<html><body><h1>这是邮件的HTML内容</h1></body></html>"
        },
        "internetMessageHeaders": {},
        "tags": []
    }
}

draft_id = create_draft(email_account, payload, access_token)
print(f'草稿ID: {draft_id}')
```

### 响应示例

```json
{
  "message": {
    "id": "DzzzzzzNpQ9",
    "subject": "测试邮件主题",
    "sentDateTime": null,
    "hasAttachments": false
  }
}
```

## 2. 创建附件上传会话

### 接口信息

- **接口名称**：CreateAttachmentUploadSession（创建上传会话（附件））
- **接口地址**：`https://alimail-cn.aliyuncs.com/v2/users/{email_account}/messages/{message_id}/attachments/createUploadSession`
- **请求方式**：`POST`
- **文档链接**：https://mailhelp.aliyun.com/openapi/index.html#/operations/alimailpb_alimail_mailagent_open_MailService_CreateAttachmentUploadSession

### 请求参数

#### Path 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `email_account` | string | 是 | 用户邮箱地址 |
| `message_id` | string | 是 | 邮件草稿ID（从 CreateMessage 接口获取） |

#### Body 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `attachment` | object | 是 | 附件信息对象 |

### 附件对象字段

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `name` | string | 是 | 附件文件名 |
| `contentId` | string | 否 | 内容ID（内联附件使用） |
| `isInline` | boolean | 否 | 是否为内联附件，默认 `false` |
| `extHeaders` | object | 否 | 扩展头信息 |

### 请求示例

```python
import requests

def create_upload_session(email_account, message_id, file_name, access_token):
    """
    创建上传会话（附件），为草稿邮件添加一个附件
    
    Args:
        email_account (str): 用户邮箱地址
        message_id (str): 邮件草稿ID
        file_name (str): 附件文件名
        access_token (str): 访问凭证
    
    Returns:
        str: 上传会话ID（从 uploadUrl 中提取）
    """
    url = f"https://alimail-cn.aliyuncs.com/v2/users/{email_account}/messages/{message_id}/attachments/createUploadSession"
    
    payload = {
        "attachment": {
            "name": file_name,
            "contentId": "string",
            "isInline": False,
            "extHeaders": {}
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'bearer {access_token}'
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    # 从 uploadUrl 中提取 session_id
    upload_url = response.json()['uploadUrl']
    # uploadUrl 格式: https://alimail-cn.aliyuncs.com/v2/stream/{session_id}
    session_id = upload_url.split('stream/')[1]
    
    return session_id
```

### 响应示例

```json
{
  "uploadUrl": "https://alimail-cn.aliyuncs.com/v2/stream/session-id-123"
}
```

## 3. 上传文件流

### 接口信息

- **接口名称**：DoUpload（上传文件流）
- **接口地址**：`https://alimail-cn.aliyuncs.com/v2/stream/{session_id}`
- **请求方式**：`POST`
- **文档链接**：https://mailhelp.aliyun.com/openapi/index.html#/operations/alimailpb_stream_StreamService_DoUpload

### 请求参数

#### Path 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `session_id` | string | 是 | 上传会话ID（从 CreateAttachmentUploadSession 接口获取） |

#### Body 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| 文件内容 | bytes | 是 | 文件的二进制内容 |

### 请求头

```
Content-Type: application/octet-stream
Authorization: bearer {access_token}
```

### 请求示例

```python
import requests

def upload_file(file_path, session_id, access_token):
    """
    上传文件流
    
    Args:
        file_path (str): 本地文件路径
        session_id (str): 上传会话ID
        access_token (str): 访问凭证
    
    Returns:
        bool: 上传是否成功
    """
    url = f"https://alimail-cn.aliyuncs.com/v2/stream/{session_id}"
    
    try:
        with open(file_path, 'rb') as file:
            payload = file.read()
    except FileNotFoundError as e:
        print(f"文件未找到：{e}")
        return False
    
    headers = {
        "Content-Type": "application/octet-stream",
        "Authorization": f'Bearer {access_token}'
    }
    
    response = requests.post(url, data=payload, headers=headers)
    response.raise_for_status()
    
    return True
```

## 4. 发送邮件

### 接口信息

- **接口名称**：SendMessage（发送草稿箱中的邮件）
- **接口地址**：`https://alimail-cn.aliyuncs.com/v2/users/{email_account}/messages/{message_id}/send`
- **请求方式**：`POST`
- **文档链接**：https://mailhelp.aliyun.com/openapi/index.html#/operations/alimailpb_alimail_mailagent_open_MailService_SendMessage

### 请求参数

#### Path 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `email_account` | string | 是 | 用户邮箱地址 |
| `message_id` | string | 是 | 邮件草稿ID |

#### Body 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `saveToSentItems` | boolean | 否 | 是否保存到已发送文件夹，默认 `true` |

### 请求头

```
Content-Type: application/json
Authorization: bearer {access_token}
```

### 请求示例

```python
import requests

def send_message(email_account, message_id, access_token, save_to_sent_items=True):
    """
    发送草稿箱中的邮件
    
    Args:
        email_account (str): 用户邮箱地址
        message_id (str): 邮件草稿ID
        access_token (str): 访问凭证
        save_to_sent_items (bool): 是否保存到已发送文件夹
    
    Returns:
        bool: 发送是否成功
    """
    url = f"https://alimail-cn.aliyuncs.com/v2/users/{email_account}/messages/{message_id}/send"
    
    payload = {
        "saveToSentItems": save_to_sent_items
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'bearer {access_token}'
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    return True
```

## 完整示例：创建邮件并发送（带附件）

```python
import email
import os
import requests

def create_and_send_message_with_attachments(
    email_account,
    subject,
    body_text,
    body_html,
    to_recipients,
    attachment_files,
    access_token
):
    """
    创建邮件并发送（支持附件）
    
    Args:
        email_account (str): 发件人邮箱地址
        subject (str): 邮件主题
        body_text (str): 纯文本正文
        body_html (str): HTML格式正文
        to_recipients (list): 收件人列表，格式：[{"email": "xxx@example.com", "name": "名称"}]
        attachment_files (list): 附件文件路径列表
        access_token (str): 访问凭证
    
    Returns:
        dict: 包含草稿ID和发送结果
    """
    # 1. 创建邮件草稿
    print('创建邮件草稿...')
    payload = {
        "message": {
            "internetMessageId": email.utils.make_msgid(),
            "subject": subject,
            "priority": "PRY_NORMAL",
            "from": {
                "email": email_account,
                "name": "发件人"
            },
            "toRecipients": to_recipients,
            "body": {
                "bodyText": body_text,
                "bodyHtml": body_html
            }
        }
    }
    
    draft_id = create_draft(email_account, payload, access_token)
    print(f'草稿创建完成，ID: {draft_id}')
    
    # 2. 上传附件
    if attachment_files:
        print(f'开始上传 {len(attachment_files)} 个附件...')
        for file_path in attachment_files:
            if not os.path.exists(file_path):
                print(f'文件不存在，跳过: {file_path}')
                continue
            
            file_name = os.path.basename(file_path)
            print(f'上传附件: {file_name}')
            
            # 创建上传会话
            session_id = create_upload_session(
                email_account, 
                draft_id, 
                file_name, 
                access_token
            )
            
            # 上传文件流
            upload_file(file_path, session_id, access_token)
            print(f'附件上传完成: {file_name}')
    
    # 3. 发送邮件
    print('发送邮件...')
    send_message(email_account, draft_id, access_token)
    print('邮件发送完成')
    
    return {
        'draft_id': draft_id,
        'sent': True
    }

# 使用示例
email_account = "test@example.com"
to_recipients = [
    {
        "email": "recipient@example.com",
        "name": "收件人"
    }
]
attachment_files = [
    r'C:\Users\Documents\file1.pdf',
    r'C:\Users\Documents\file2.txt'
]

result = create_and_send_message_with_attachments(
    email_account=email_account,
    subject="测试邮件",
    body_text="这是邮件的纯文本内容",
    body_html="<html><body><h1>这是邮件的HTML内容</h1></body></html>",
    to_recipients=to_recipients,
    attachment_files=attachment_files,
    access_token=access_token
)

print(f'邮件已发送，草稿ID: {result["draft_id"]}')
```

## 注意事项

1. **批量发送建议**：批量或系统类邮件建议使用邮件推送产品（SMTP或API发信方式），而不是企业邮箱API接口
2. **接口联动**：企业邮箱API接口发信需要多个接口联动，适合特殊场景使用
3. **文件大小限制**：注意附件文件大小限制，避免上传失败
4. **文件类型**：上传的附件是字节流（bytes）类型，需要使用二进制模式读取文件
5. **错误处理**：需要妥善处理网络请求异常、文件读取异常等情况
6. **草稿保存**：创建草稿后，如果不发送，草稿会保存在草稿箱中

## 相关文档

- [阿里邮箱 API 开放平台官方文档](https://mailhelp.aliyun.com/openapi/index.html)
- [API开放平台场景示例：创建草稿并发送邮件](https://help.aliyun.com/document_detail/2856076.html)
- [API开放平台场景示例：创建草稿并上传附件](https://help.aliyun.com/document_detail/2856471.html)
