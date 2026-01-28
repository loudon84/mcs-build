# 获取邮箱文件夹列表和邮件列表

## 概述

本文档说明如何使用阿里邮箱开放平台 API 获取邮箱文件夹列表，以及获取指定文件夹内的所有邮件列表。

## 前置条件

1. 已完成 OAuth 授权，获取到 `access_token`
2. 应用已获得相应的接口权限（邮件读取权限）

## 1. 获取邮箱文件夹列表

### 接口信息

- **接口名称**：ListMailFolders（列出邮件文件夹）
- **接口地址**：`https://alimail-cn.aliyuncs.com/v2/users/{email_account}/mailFolders`
- **请求方式**：`GET`
- **文档链接**：https://mailhelp.aliyun.com/openapi/index.html#/operations/alimailpb_alimail_mailagent_open_MailFolderService_ListMailFolders

### 请求参数

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| `email_account` | string | Path | 是 | 用户邮箱地址 |

### 请求头

```
Content-Type: application/json
Authorization: bearer {access_token}
```

### 请求示例

```python
import requests

def list_mail_folders(email_account, access_token):
    """
    获取邮箱文件夹列表
    
    Args:
        email_account (str): 用户邮箱地址
        access_token (str): 访问凭证
    
    Returns:
        dict: 文件夹列表的JSON响应
    """
    url = f"https://alimail-cn.aliyuncs.com/v2/users/{email_account}/mailFolders"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'bearer {access_token}'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json()
```

### 响应示例

```json
{
  "value": [
    {
      "id": "1",
      "displayName": "发件箱",
      "childFolderCount": 0,
      "unreadItemCount": 5,
      "totalItemCount": 100
    },
    {
      "id": "2",
      "displayName": "收件箱",
      "childFolderCount": 0,
      "unreadItemCount": 10,
      "totalItemCount": 200
    }
  ]
}
```

### 常用文件夹 ID

根据阿里邮箱的规范，以下是一些常用文件夹的标准 ID：

| 文件夹名称 | 文件夹 ID |
|-----------|----------|
| 发件箱 | `1` |
| 收件箱 | `2` |
| 垃圾箱 | `3` |
| 草稿箱 | `5` |
| 已删除 | `6` |

## 2. 获取指定文件夹内的邮件列表

### 接口信息

- **接口名称**：ListMessages（批量获取指定文件夹下的邮件列表）
- **接口地址**：`https://alimail-cn.aliyuncs.com/v2/users/{email_account}/mailFolders/{folder_id}/messages`
- **请求方式**：`GET`
- **文档链接**：https://mailhelp.aliyun.com/openapi/index.html#/operations/alimailpb_alimail_mailagent_open_MailService_ListMessages

### 请求参数

#### Path 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `email_account` | string | 是 | 用户邮箱地址 |
| `folder_id` | string | 是 | 邮件文件夹ID |

#### Query 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `cursor` | string | 否 | 游标，用于分页获取数据。首次请求为空字符串，后续请求使用响应中的 `nextCursor` |
| `size` | integer | 否 | 每页返回的邮件数量，最大值为 100，默认为 100 |
| `orderby` | string | 否 | 排序方式，可选值：`ASC`（升序）、`DES`（降序），默认为 `DES` |

### 请求头

```
Content-Type: application/json
Authorization: bearer {access_token}
```

### 请求示例

```python
import requests

def list_messages(email_account, folder_id, access_token, cursor="", size=100, orderby="DES"):
    """
    批量获取指定文件夹下的邮件列表，每次最多获取100封邮件
    
    Args:
        email_account (str): 用户邮箱地址
        folder_id (str): 邮件文件夹ID
        access_token (str): 访问凭证
        cursor (str): 游标，用于分页获取数据
        size (int): 每页返回的邮件数量，最大值为100
        orderby (str): 排序方式，ASC或DES
    
    Returns:
        dict: 邮件列表的JSON响应
    """
    url = f"https://alimail-cn.aliyuncs.com/v2/users/{email_account}/mailFolders/{folder_id}/messages"
    
    querystring = {
        "cursor": cursor,
        "size": str(size),
        "orderby": orderby
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'bearer {access_token}'
    }
    
    response = requests.get(url, headers=headers, params=querystring)
    response.raise_for_status()
    
    return response.json()
```

### 响应参数

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `messages` | array | 邮件列表 |
| `hasMore` | boolean | 是否还有更多数据 |
| `nextCursor` | string | 下一页的游标，用于继续获取数据 |

### 邮件对象字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | string | 邮件ID |
| `mailId` | string | 邮件唯一标识 |
| `subject` | string | 邮件主题 |
| `sentDateTime` | string | 发送时间（ISO 8601格式，与北京时间时差8小时） |
| `receivedDateTime` | string | 接收时间 |
| `hasAttachments` | boolean | 是否有附件 |
| `isRead` | boolean | 是否已读 |
| `from` | object | 发件人信息 |
| `toRecipients` | array | 收件人列表 |
| `ccRecipients` | array | 抄送人列表 |
| `bccRecipients` | array | 密送人列表 |

### 响应示例

```json
{
  "messages": [
    {
      "id": "DzzzzzzNpQ9",
      "mailId": "mail-id-123",
      "subject": "测试邮件",
      "sentDateTime": "2024-01-01T10:00:00Z",
      "receivedDateTime": "2024-01-01T10:00:01Z",
      "hasAttachments": true,
      "isRead": false,
      "from": {
        "email": "sender@example.com",
        "name": "发件人"
      },
      "toRecipients": [
        {
          "email": "recipient@example.com",
          "name": "收件人"
        }
      ]
    }
  ],
  "hasMore": true,
  "nextCursor": "cursor-string-for-next-page"
}
```

## 3. 获取所有邮件（分页处理）

由于单次请求最多只能获取 100 封邮件，如果需要获取文件夹内的所有邮件，需要进行分页处理。

### Python 示例代码

```python
def get_all_messages(email_account, folder_id, access_token):
    """
    获取指定文件夹内的所有邮件
    
    Args:
        email_account (str): 用户邮箱地址
        folder_id (str): 邮件文件夹ID
        access_token (str): 访问凭证
    
    Returns:
        list: 所有邮件的列表
    """
    records = []
    cursor = ""
    
    while True:
        # 获取数据
        parsed_data = list_messages(email_account, folder_id, access_token, cursor=cursor)
        
        # 提取所需字段
        for v_mail in parsed_data['messages']:
            record = {
                'id': v_mail['id'],
                'mailId': v_mail['mailId'],
                'sentDateTime': v_mail['sentDateTime'],  # 注意：和北京时间时差8小时
                'hasAttachments': v_mail['hasAttachments'],
                'subject': v_mail.get('subject', ''),
                'isRead': v_mail.get('isRead', False)
            }
            records.append(record)
        
        # 更新游标
        cursor = parsed_data.get("nextCursor", "")
        has_more = parsed_data.get("hasMore", False)
        
        print(f'hasMore={has_more}, nextCursor={cursor}')
        
        if not has_more:
            print('没有更多数据')
            break
    
    return records

# 使用示例
email_account = 'test@example.com'
folder_id = "2"  # 收件箱
all_messages = get_all_messages(email_account, folder_id, access_token)
print(f'邮件基本信息：共{len(all_messages)}封')
```

## 注意事项

1. **时区问题**：`sentDateTime` 和 `receivedDateTime` 字段返回的时间与北京时间相差 8 小时，需要根据实际情况进行时区转换
2. **分页限制**：单次请求最多返回 100 封邮件，需要根据 `hasMore` 和 `nextCursor` 进行分页处理
3. **文件夹 ID**：建议先调用 `ListMailFolders` 接口获取准确的文件夹 ID，而不是硬编码使用标准 ID
4. **错误处理**：需要妥善处理网络请求异常和响应解析异常

## 相关文档

- [阿里邮箱 API 开放平台官方文档](https://mailhelp.aliyun.com/openapi/index.html)
- [API开放平台场景示例：列出邮件和附件并下载附件](https://help.aliyun.com/document_detail/2856396.html)
