# 阿里邮箱 OAuth 授权与 Token 获取

## 概述

阿里邮箱 API 开放平台采用 OAuth 2.0 授权机制获取访问凭证。在使用其他 API 接口之前，必须先完成 OAuth 授权流程并获取 `access_token`。

## 前置条件

1. **版本要求**：免费版不支持 API 开放平台功能，需要使用付费版本
2. **管理员权限**：需要邮箱管理员权限来创建应用

## 获取应用凭证

### 步骤 1：创建应用

1. 管理员登录**邮箱管理后台**
2. 进入**高级应用** → **API开放平台**
3. 点击**添加应用**
4. 勾选需要的接口权限（如邮件读取、发送等）
5. 保存应用配置

### 步骤 2：获取应用凭证

创建应用后，再次编辑进入应用详情页面，即可获得：

- **应用ID** (`client_id`)
- **应用Secret** (`client_secret`)

## 获取访问凭证 (Token)

### 接口信息

- **接口地址**：`https://alimail-cn.aliyuncs.com/oauth2/v2.0/token`
- **请求方式**：`POST`
- **Content-Type**：`application/x-www-form-urlencoded`

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `grant_type` | string | 是 | 固定值：`client_credentials` |
| `client_id` | string | 是 | 应用ID |
| `client_secret` | string | 是 | 应用Secret |

### 请求示例

```bash
curl -X POST "https://alimail-cn.aliyuncs.com/oauth2/v2.0/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"
```

### Python 示例代码

```python
# -*- coding: utf-8 -*-
import os
import requests
from datetime import datetime, timedelta

def get_access_token():
    """
    获取访问凭证。本函数通过请求阿里云邮箱的OAuth2.0接口获取访问凭证（access_token）。
    需要使用环境变量中的客户端ID和客户端密钥进行认证。
    
    Returns:
        str: 访问凭证 access_token
    """
    # 打印接口名称和文档链接
    print('接口名称：获取访问凭证')
    print('文档：https://mailhelp.aliyun.com/openapi/index.html#/markdown/authorization.md')
    
    # 定义接口URL
    interface_url = "https://alimail-cn.aliyuncs.com/oauth2/v2.0/token"
    
    # 设置请求头，指定内容类型
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    # 从环境变量中获取客户端ID和密钥
    client_id = os.getenv('ALIMAIL_CLIENT_ID')
    client_secret = os.getenv('ALIMAIL_CLIENT_SECRET')
    
    # 检查客户端ID和密钥是否已设置
    if not client_id or not client_secret:
        raise ValueError("Environment variables ALIMAIL_CLIENT_ID and ALIMAIL_CLIENT_SECRET must be set!")
    
    # 准备请求数据
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        # 发送POST请求
        response = requests.post(interface_url, headers=headers, data=data)
        
        # 打印接口返回参数
        print(f'接口返回参数：{response.json()}')
        
        # 解析响应为字典
        response_json = response.json()
        
        # 提取token类型和过期时间
        token_type = response_json["token_type"]
        expires_in = response_json["expires_in"]
        
        # 打印token类型
        print(f'token_type: {token_type}')
        
        # 计算过期时间
        current_time = datetime.now()
        expiration_time = current_time + timedelta(seconds=expires_in)
        
        # 打印过期时间
        print(f"expires_in: {round(expires_in / 3600)} hours, end_time: {expiration_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 返回访问凭证
        return response_json["access_token"]
        
    except requests.RequestException as e:
        # 处理请求失败异常
        print(f"请求失败：{e}")
        raise
    except (KeyError, ValueError) as e:
        # 处理解析响应失败异常
        print(f"解析响应失败：{e}")
        raise

# 调用函数获取访问凭证并打印
if __name__ == "__main__":
    access_token = get_access_token()
    print(f'access_token: {access_token}')
```

### 响应参数

成功响应包含以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `access_token` | string | 访问凭证，用于后续 API 调用 |
| `token_type` | string | 令牌类型，通常为 `Bearer` |
| `expires_in` | integer | 有效期（单位：秒） |

### 响应示例

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

## 使用 Token

获取到 `access_token` 后，在调用其他 API 接口时，需要在请求头中携带：

```
Authorization: bearer {access_token}
```

### 示例

```python
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'bearer {access_token}'
}
```

## 注意事项

1. **Token 有效期**：`access_token` 具有有效期（通常为 3600 秒），过期后需要重新获取
2. **环境变量配置**：建议将 `client_id` 和 `client_secret` 存储在环境变量中，不要硬编码在代码中
3. **错误处理**：需要妥善处理网络请求异常和响应解析异常
4. **安全性**：`client_secret` 属于敏感信息，请妥善保管，不要泄露

## 相关文档

- [阿里邮箱 API 开放平台官方文档](https://mailhelp.aliyun.com/openapi/index.html#/markdown/authorization.md)
- [阿里云帮助中心 - API开放平台代码示例：获取访问凭证](https://help.aliyun.com/document_detail/2855420.html)
