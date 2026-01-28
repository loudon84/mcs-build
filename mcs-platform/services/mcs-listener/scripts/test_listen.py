#!/usr/bin/env python3
"""测试脚本：读取 .env 配置并测试邮箱监听功能。"""

import asyncio
import os
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# 添加 contracts 库到 Python 路径（作为 mcs_contracts 包）
contracts_src = project_root.parent.parent / "libs" / "contracts" / "src"
if contracts_src.exists():
    sys.path.insert(0, str(contracts_src))

# 添加 contracts 库到 Python 路径
contracts_path = project_root.parent.parent / "libs" / "contracts" / "src"
if contracts_path.exists():
    sys.path.insert(0, str(contracts_path))

from settings import Settings
from scheduler import UnifiedScheduler
from db.engine import create_db_engine, create_session_factory
from db.repo import ListenerRepo


async def test_listen():
    """测试邮箱监听功能。"""
    print("=" * 60)
    print("MCS Listener - 邮箱监听测试")
    print("=" * 60)
    
    # 确保从项目根目录读取 .env
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"✓ 找到 .env 文件: {env_file}")
        # 设置工作目录为项目根目录，确保 pydantic-settings 能找到 .env
        os.chdir(project_root)
    else:
        print(f"⚠ 警告: 未找到 .env 文件: {env_file}")
        print("   将使用环境变量或默认配置")
    
    # 读取配置
    print("\n读取配置...")
    try:
        settings = Settings.from_env()
        print(f"✓ 配置读取成功")
    except Exception as e:
        print(f"✗ 配置读取失败: {e}")
        return
    
    # 显示配置信息
    print("\n配置信息:")
    print(f"  应用环境: {settings.app_env}")
    print(f"  日志级别: {settings.log_level}")
    print(f"  启用的监听器: {settings.enabled_listeners}")
    print(f"  邮件提供商: {settings.email_provider}")
    
    if settings.email_provider == "alimail":
        print(f"\n阿里邮箱配置:")
        print(f"  Client ID: {settings.alimail_client_id[:10]}..." if settings.alimail_client_id else "  Client ID: (未设置)")
        print(f"  Email Account: {settings.alimail_email_account}")
        print(f"  Folder ID: {settings.alimail_folder_id}")
        print(f"  Poll Size: {settings.alimail_poll_size}")
    elif settings.email_provider == "imap":
        print(f"\nIMAP 配置:")
        print(f"  Host: {settings.imap_host}")
        print(f"  Port: {settings.imap_port}")
        print(f"  User: {settings.imap_user}")
    
    print(f"\n数据库配置:")
    print(f"  DSN: {settings.db_dsn.split('@')[0]}@***" if '@' in settings.db_dsn else f"  DSN: {settings.db_dsn}")
    
    print(f"\n编排器 API:")
    print(f"  URL: {settings.orchestrator_api_url}")
    
    # 检查必要配置
    print("\n检查配置完整性...")
    if "email" in settings.get_enabled_listeners():
        if settings.email_provider == "alimail":
            if not settings.alimail_client_id or not settings.alimail_client_secret:
                print("✗ 错误: 阿里邮箱 Client ID 或 Client Secret 未设置")
                return
            if not settings.alimail_email_account:
                print("✗ 错误: 阿里邮箱账户未设置")
                return
            print("✓ 阿里邮箱配置完整")
        elif settings.email_provider == "imap":
            if not settings.imap_host or not settings.imap_user:
                print("✗ 错误: IMAP 配置不完整")
                return
            print("✓ IMAP 配置完整")
    else:
        print("⚠ 警告: 未启用 email 监听器")
        return
    
    # 测试数据库连接
    print("\n测试数据库连接...")
    try:
        engine = create_db_engine(settings)
        session_factory = create_session_factory(engine)
        session = session_factory()
        session.close()
        print("✓ 数据库连接成功")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        print("  提示: 请确保 PostgreSQL 数据库已启动，并运行 'alembic upgrade head' 创建表")
        return
    
    # 初始化调度器
    print("\n初始化调度器...")
    try:
        repo = ListenerRepo(session_factory())
        scheduler = UnifiedScheduler(settings, repo=repo)
        print("✓ 调度器初始化成功")
    except Exception as e:
        print(f"✗ 调度器初始化失败: {e}")
        return
    
    # 测试邮箱连接
    print("\n测试邮箱连接...")
    try:
        await scheduler.start()
        print("✓ 调度器启动成功")
        
        # 等待一下，让调度器初始化监听器
        await asyncio.sleep(2)
        
        # 手动触发一次轮询
        print("\n执行一次邮箱轮询...")
        await scheduler._poll_email()
        print("✓ 邮箱轮询完成")
        
        # 等待一段时间观察
        print("\n监听器已启动，等待 10 秒观察日志...")
        print("(按 Ctrl+C 停止)")
        await asyncio.sleep(10)
        
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n停止调度器...")
        await scheduler.stop()
        print("✓ 调度器已停止")


if __name__ == "__main__":
    asyncio.run(test_listen())
