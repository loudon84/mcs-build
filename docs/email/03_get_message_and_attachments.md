# 获取邮件内容和附件

## 概述

本文档说明如何使用阿里邮箱开放平台 API 获取邮件详细内容、列出邮件附件，以及下载附件。

## 前置条件

1. 已完成 OAuth 授权，获取到 `access_token`
2. 应用已获得相应的接口权限（邮件读取权限）
3. 已获取到邮件 ID（通过 ListMessages 接口）

## 1. 获取邮件详细内容

### 接口信息

- **接口名称**：GetMessage（获取邮件详情）
- **接口地址**：`https://alimail-cn.aliyuncs.com/v2/users/{email_account}/messages/{message_id}`
- **请求方式**：`GET`
- **文档链接**：https://mailhelp.aliyun.com/openapi/index.html#/operations/alimailpb_alimail_mailagent_open_MailService_GetMessage

### 请求参数

#### Path 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `email_account` | string | 是 | 用户邮箱地址 |
| `message_id` | string | 是 | 邮件ID（从 ListMessages 接口获取） |

### 请求头

```
Content-Type: application/json
Authorization: bearer {access_token}
```

### 请求示例

```python
import requests

def get_message(email_account, message_id, access_token):
    """
    获取邮件详细内容
    
    Args:
        email_account (str): 用户邮箱地址
        message_id (str): 邮件ID
        access_token (str): 访问凭证
    
    Returns:
        dict: 邮件详细信息的JSON响应
    """
    url = f"https://alimail-cn.aliyuncs.com/v2/users/{email_account}/messages/{message_id}"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'bearer {access_token}'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json()
```

### 响应参数

邮件对象包含以下主要字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | string | 邮件ID |
| `mailId` | string | 邮件唯一标识 |
| `subject` | string | 邮件主题 |
| `sentDateTime` | string | 发送时间 |
| `receivedDateTime` | string | 接收时间 |
| `body` | object | 邮件正文 |
| `body.bodyText` | string | 纯文本正文 |
| `body.bodyHtml` | string | HTML格式正文 |
| `from` | object | 发件人信息 |
| `toRecipients` | array | 收件人列表 |
| `ccRecipients` | array | 抄送人列表 |
| `bccRecipients` | array | 密送人列表 |
| `replyTo` | array | 回复地址列表 |
| `hasAttachments` | boolean | 是否有附件 |
| `attachments` | array | 附件列表（如果包含） |

### 响应示例

```json
{
  "id": "DzzzzzzNpQ9",
  "mailId": "mail-id-123",
  "subject": "测试邮件",
  "sentDateTime": "2024-01-01T10:00:00Z",
  "receivedDateTime": "2024-01-01T10:00:01Z",
  "hasAttachments": true,
  "body": {
    "bodyText": "这是邮件的纯文本内容",
    "bodyHtml": "<html><body><h1>这是邮件的HTML内容</h1></body></html>"
  },
  "from": {
    "email": "sender@example.com",
    "name": "发件人"
  },
  "toRecipients": [
    {
      "email": "recipient@example.com",
      "name": "收件人"
    }
  ],
  "ccRecipients": [],
  "bccRecipients": [],
  "replyTo": []
}
```

## 2. 列出邮件的所有附件

### 接口信息

- **接口名称**：ListAttachments（列出邮件的全部附件）
- **接口地址**：`https://alimail-cn.aliyuncs.com/v2/users/{email_account}/messages/{message_id}/attachments`
- **请求方式**：`GET`
- **文档链接**：https://mailhelp.aliyun.com/openapi/index.html#/operations/alimailpb_alimail_mailagent_open_MailService_ListAttachments

### 请求参数

#### Path 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `email_account` | string | 是 | 用户邮箱地址 |
| `message_id` | string | 是 | 邮件ID |

### 请求头

```
Content-Type: application/json
Authorization: bearer {access_token}
```

### 请求示例

```python
import requests

def list_attachments(email_account, message_id, access_token):
    """
    列出邮件的全部附件
    
    Args:
        email_account (str): 用户邮箱地址
        message_id (str): 邮件ID
        access_token (str): 访问凭证
    
    Returns:
        list: 附件列表
    """
    url = f"https://alimail-cn.aliyuncs.com/v2/users/{email_account}/messages/{message_id}/attachments"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'bearer {access_token}'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json()['attachments']
```

### 响应参数

附件对象包含以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | string | 附件ID，用于下载附件 |
| `name` | string | 附件文件名 |
| `contentType` | string | 附件MIME类型 |
| `size` | integer | 附件大小（字节） |
| `isInline` | boolean | 是否为内联附件 |
| `contentId` | string | 内容ID（内联附件使用） |

### 响应示例

```json
{
  "attachments": [
    {
      "id": "attachment-id-1",
      "name": "document.pdf",
      "contentType": "application/pdf",
      "size": 102400,
      "isInline": false,
      "contentId": null
    },
    {
      "id": "attachment-id-2",
      "name": "image.jpg",
      "contentType": "image/jpeg",
      "size": 51200,
      "isInline": true,
      "contentId": "cid:image1"
    }
  ]
}
```

## 3. 下载附件

### 接口信息

- **接口名称**：CreateAttachmentDownloadSession（创建下载会话并下载附件）
- **接口地址**：`https://alimail-cn.aliyuncs.com/v2/users/{email_account}/messages/{message_id}/attachments/{attachment_id}/$value`
- **请求方式**：`GET`
- **文档链接**：https://mailhelp.aliyun.com/openapi/index.html#/operations/alimailpb_alimail_mailagent_open_MailService_CreateAttachmentDownloadSession

### 请求参数

#### Path 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `email_account` | string | 是 | 用户邮箱地址 |
| `message_id` | string | 是 | 邮件ID |
| `attachment_id` | string | 是 | 附件ID（从 ListAttachments 接口获取） |

### 请求头

```
Content-Type: application/json
Authorization: bearer {access_token}
```

### 请求示例

```python
import requests

def download_attachment(email_account, message_id, attachment_id, save_path, access_token):
    """
    创建下载会话（附件）并下载附件
    
    Args:
        email_account (str): 用户邮箱地址
        message_id (str): 邮件ID
        attachment_id (str): 附件ID
        save_path (str): 保存附件的本地路径（包含文件名）
        access_token (str): 访问凭证
    
    Returns:
        bool: 下载是否成功
    """
    url = f"https://alimail-cn.aliyuncs.com/v2/users/{email_account}/messages/{message_id}/attachments/{attachment_id}/$value"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'bearer {access_token}'
    }
    
    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()
    
    # 保存附件到本地文件
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    return True
```

### 下载流程

1. 调用 `ListAttachments` 接口获取附件列表
2. 从附件列表中提取 `attachment_id` 和 `name`
3. 调用下载接口，使用 `attachment_id` 下载附件
4. 将响应内容保存为文件

## 完整示例：获取邮件并下载所有附件

```python
import requests
import os

def get_message_and_download_attachments(email_account, message_id, access_token, download_dir="./downloads"):
    """
    获取邮件内容并下载所有附件
    
    Args:
        email_account (str): 用户邮箱地址
        message_id (str): 邮件ID
        access_token (str): 访问凭证
        download_dir (str): 附件下载目录
    
    Returns:
        dict: 包含邮件信息和下载结果
    """
    # 确保下载目录存在
    os.makedirs(download_dir, exist_ok=True)
    
    # 1. 获取邮件详细内容
    print(f'获取邮件内容: {message_id}')
    message = get_message(email_account, message_id, access_token)
    print(f'邮件主题: {message.get("subject", "")}')
    
    # 2. 检查是否有附件
    if not message.get('hasAttachments', False):
        print('该邮件没有附件')
        return {
            'message': message,
            'attachments': []
        }
    
    # 3. 列出所有附件
    print('获取附件列表...')
    attachments = list_attachments(email_account, message_id, access_token)
    print(f'找到 {len(attachments)} 个附件')
    
    # 4. 下载所有附件
    downloaded_files = []
    for attachment in attachments:
        attachment_id = attachment['id']
        attachment_name = attachment['name']
        save_path = os.path.join(download_dir, attachment_name)
        
        print(f'下载附件: {attachment_name}')
        try:
            download_attachment(
                email_account, 
                message_id, 
                attachment_id, 
                save_path, 
                access_token
            )
            downloaded_files.append({
                'name': attachment_name,
                'path': save_path,
                'size': attachment.get('size', 0)
            })
            print(f'下载完成: {save_path}')
        except Exception as e:
            print(f'下载失败 {attachment_name}: {e}')
    
    return {
        'message': message,
        'attachments': downloaded_files
    }

# 使用示例
email_account = 'test@example.com'
message_id = 'DzzzzzzNpQ9'  # 从 ListMessages 接口获取

result = get_message_and_download_attachments(
    email_account, 
    message_id, 
    access_token,
    download_dir='./attachments'
)

print(f'邮件主题: {result["message"]["subject"]}')
print(f'下载了 {len(result["attachments"])} 个附件')
```

## 注意事项

1. **文件大小**：下载大文件时，建议使用 `stream=True` 参数进行流式下载，避免内存溢出
2. **文件路径**：保存附件时，注意处理文件名中的特殊字符，避免路径错误
3. **错误处理**：需要妥善处理网络请求异常、文件写入异常等情况
4. **并发下载**：如果需要下载多个附件，可以考虑使用多线程或异步方式提高效率
5. **文件覆盖**：如果附件文件名相同，后下载的文件会覆盖先下载的文件，建议添加时间戳或序号

## 相关文档

- [阿里邮箱 API 开放平台官方文档](https://mailhelp.aliyun.com/openapi/index.html)
- [API开放平台场景示例：列出邮件和附件并下载附件](https://help.aliyun.com/document_detail/2856396.html)
