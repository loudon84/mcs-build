#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试邮箱监听功能。"""

import asyncio
import os
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# 添加 contracts 库到 Python 路径
contracts_src = project_root.parent.parent / "libs" / "contracts" / "src"
if contracts_src.exists():
    sys.path.insert(0, str(contracts_src))

# 确保从项目根目录读取 .env
os.chdir(project_root)

print("=" * 60)
print("MCS Listener - Email Listening Test")
print("=" * 60)

# 读取配置
print("\nLoading configuration...")
try:
    from settings import Settings
    settings = Settings.from_env()
    print("[OK] Configuration loaded")
except Exception as e:
    print(f"[ERROR] Failed to load configuration: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 显示配置
print(f"\nEmail Provider: {settings.email_provider}")
print(f"Enabled Listeners: {settings.enabled_listeners}")

if settings.email_provider == "alimail":
    print(f"Alimail Account: {settings.alimail_email_account}")
    print(f"Folder ID: {settings.alimail_folder_id}")

# 测试邮箱连接和轮询
print("\nTesting email listener...")
try:
    from listeners.alimail_listener import AlimailListener
    from listeners.email import EmailListener
    
    if settings.email_provider == "alimail":
        listener = AlimailListener(
            client_id=settings.alimail_client_id,
            client_secret=settings.alimail_client_secret,
            email_account=settings.alimail_email_account,
            folder_id=settings.alimail_folder_id,
            base_url=settings.alimail_api_base_url,
            poll_size=settings.alimail_poll_size,
        )
    else:
        listener = EmailListener(
            provider=settings.email_provider,
            host=settings.imap_host,
            port=settings.imap_port,
            user=settings.imap_user,
            password=settings.imap_pass,
        )
    
    async def test():
        print("\nConnecting to email server...")
        await listener.connect()
        print("[OK] Connected")
        
        print("\nPolling for new messages...")
        uids = await listener.poll_new_messages()
        print(f"[OK] Found {len(uids)} new messages")
        
        if uids:
            print(f"\nFetching first message (UID: {uids[0]})...")
            message_data = await listener.fetch_message(uids[0])
            print(f"[OK] Message fetched")
            print(f"  Subject: {message_data.get('subject', 'N/A')}")
            print(f"  From: {message_data.get('from', 'N/A')}")
            print(f"  Has attachments: {len(message_data.get('attachments', [])) > 0}")
        else:
            print("No new messages found")
        
        await listener.disconnect()
        print("\n[OK] Disconnected")
    
    asyncio.run(test())
    
except Exception as e:
    print(f"\n[ERROR] Failed: {e}")
    import traceback
    traceback.print_exc()
    
    # 如果是 OAuth 错误，提供更多信息
    if "AlimailAuthError" in str(type(e)):
        print("\n提示:")
        print("1. 检查 .env 文件中的 ALIMAIL_CLIENT_ID 和 ALIMAIL_CLIENT_SECRET 是否正确")
        print("2. 确认这些凭证是从阿里邮箱管理后台的 API 开放平台获取的")
        print("3. 确认应用已启用相应的 API 权限")
    
    sys.exit(1)

print("\n[OK] Test completed successfully!")
