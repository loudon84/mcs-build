#!/usr/bin/env python3
"""简单测试脚本：读取 .env 配置并显示配置信息。"""

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
print("MCS Listener - 配置读取测试")
print("=" * 60)

# 检查 .env 文件
env_file = project_root / ".env"
if env_file.exists():
    print(f"[OK] 找到 .env 文件: {env_file}")
else:
    print(f"[WARN] 未找到 .env 文件: {env_file}")
    print("   将使用环境变量或默认配置")

# 读取配置
print("\n读取配置...")
try:
    from settings import Settings
    settings = Settings.from_env()
    print("[OK] 配置读取成功")
except Exception as e:
    print(f"✗ 配置读取失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 显示配置信息
print("\n配置信息:")
print(f"  应用环境: {settings.app_env}")
print(f"  日志级别: {settings.log_level}")
print(f"  启用的监听器: {settings.enabled_listeners}")
print(f"  邮件提供商: {settings.email_provider}")

if settings.email_provider == "alimail":
    print(f"\n阿里邮箱配置:")
    print(f"  Client ID: {settings.alimail_client_id[:15]}..." if settings.alimail_client_id and len(settings.alimail_client_id) > 15 else f"  Client ID: {settings.alimail_client_id or '(未设置)'}")
    print(f"  Client Secret: {'已设置' if settings.alimail_client_secret else '(未设置)'}")
    print(f"  Email Account: {settings.alimail_email_account or '(未设置)'}")
    print(f"  Folder ID: {settings.alimail_folder_id}")
    print(f"  Poll Size: {settings.alimail_poll_size}")
    print(f"  API Base URL: {settings.alimail_api_base_url}")
elif settings.email_provider == "imap":
    print(f"\nIMAP 配置:")
    print(f"  Host: {settings.imap_host}")
    print(f"  Port: {settings.imap_port}")
    print(f"  User: {settings.imap_user or '(未设置)'}")

print(f"\n数据库配置:")
if '@' in settings.db_dsn:
    parts = settings.db_dsn.split('@')
    print(f"  DSN: {parts[0]}@***")
else:
    print(f"  DSN: {settings.db_dsn}")

print(f"\n编排器 API:")
print(f"  URL: {settings.orchestrator_api_url}")
print(f"  API Key: {'已设置' if settings.orchestrator_api_key else '(未设置)'}")

print(f"\n轮询配置:")
print(f"  轮询间隔: {settings.poll_interval_seconds} 秒")

# 检查必要配置
print("\n检查配置完整性...")
errors = []
if "email" in settings.get_enabled_listeners():
    if settings.email_provider == "alimail":
        if not settings.alimail_client_id:
            errors.append("阿里邮箱 Client ID 未设置")
        if not settings.alimail_client_secret:
            errors.append("阿里邮箱 Client Secret 未设置")
        if not settings.alimail_email_account:
            errors.append("阿里邮箱账户未设置")
        if not errors:
            print("[OK] 阿里邮箱配置完整")
    elif settings.email_provider == "imap":
        if not settings.imap_host:
            errors.append("IMAP Host 未设置")
        if not settings.imap_user:
            errors.append("IMAP User 未设置")
        if not errors:
            print("[OK] IMAP 配置完整")
else:
    print("[WARN] 未启用 email 监听器")

if errors:
    print("\n[ERROR] 配置错误:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)

print("\n[OK] 配置检查通过！")
print("\n提示: 运行 'python scripts/test_listen.py' 可以测试邮箱监听功能")
