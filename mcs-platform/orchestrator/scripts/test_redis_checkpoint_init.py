#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立测试脚本：测试 RedisCheckpointStore 初始化。

使用方法：
    conda activate mcs-platform
    cd e:\\git-ai\\mcs-agent\\mcs-platform\\orchestrator
    python scripts/test_redis_checkpoint_init.py

或者直接运行：
    python -m scripts.test_redis_checkpoint_init
"""

import asyncio
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
_project_root = Path(__file__).resolve().parent.parent
_src_dir = _project_root / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from db.checkpoint.redis_checkpoint import RedisCheckpointStore
from settings import Settings


async def test_redis_connection():
    """测试 Redis 连接（基础测试）。"""
    print("=" * 80)
    print("Redis 连接测试")
    print("=" * 80)
    print()
    
    print("步骤 1: 加载配置...")
    try:
        settings = Settings.from_env()
        redis_url = settings.redis_url
        # 隐藏密码
        safe_url = redis_url.split("@")[-1] if "@" in redis_url else redis_url
        print(f"  [OK] 配置加载成功")
        print(f"  - Redis URL: {safe_url}")
        print()
    except Exception as e:
        print(f"  [FAIL] 配置加载失败: {e}")
        return False
    
    print("步骤 2: 测试 Redis 连接...")
    try:
        import redis.asyncio as redis
        
        # 创建 Redis 客户端
        client = await redis.from_url(redis_url, decode_responses=True)
        
        # 测试连接
        result = await client.ping()
        if result:
            print(f"  [OK] Redis 连接成功")
            print(f"  - PING 响应: {result}")
        else:
            print(f"  [FAIL] Redis PING 失败")
            await client.close()
            return False
        
        # 测试基本操作
        test_key = "test:checkpoint:connection"
        await client.set(test_key, "test_value", ex=10)  # 10秒过期
        value = await client.get(test_key)
        if value == "test_value":
            print(f"  [OK] Redis 读写测试成功")
            print(f"  - 测试键: {test_key}")
            print(f"  - 测试值: {value}")
        else:
            print(f"  [FAIL] Redis 读写测试失败")
            await client.close()
            return False
        
        await client.close()
        print()
    except Exception as e:
        print(f"  [FAIL] Redis 连接测试失败: {e}")
        print(f"  - 错误类型: {type(e).__name__}")
        import traceback
        print(f"  - 详细错误:")
        traceback.print_exc()
        return False
    
    print("=" * 80)
    print("[SUCCESS] Redis 连接测试通过！")
    print("=" * 80)
    print()
    return True


async def test_redis_checkpoint_initialization():
    """测试 RedisCheckpointStore 初始化过程。"""
    print("=" * 80)
    print("RedisCheckpointStore 初始化测试")
    print("=" * 80)
    print()

    # 1. 加载配置
    print("步骤 1: 加载配置...")
    try:
        settings = Settings.from_env()
        redis_url = settings.redis_url
        # 隐藏密码
        safe_url = redis_url.split("@")[-1] if "@" in redis_url else redis_url
        print(f"  [OK] 配置加载成功")
        print(f"  - Redis URL: {safe_url}")
        print()
    except Exception as e:
        print(f"  [FAIL] 配置加载失败: {e}")
        return False

    # 2. 创建 RedisCheckpointStore
    print("步骤 2: 创建 RedisCheckpointStore 实例...")
    try:
        checkpoint_store = RedisCheckpointStore(settings)
        print(f"  [OK] RedisCheckpointStore 实例创建成功")
        print(f"  - Redis URL: {checkpoint_store.redis_url.split('@')[-1] if '@' in checkpoint_store.redis_url else '***'}")
        print()
    except Exception as e:
        print(f"  [FAIL] 创建实例失败: {e}")
        return False

    # 3. 初始化（这是可能卡住的地方）
    print("步骤 3: 初始化 checkpoint store（创建 Redis 连接和 AsyncRedisSaver）...")
    print("  这可能需要几秒钟...")
    try:
        import time
        start_time = time.time()
        
        await checkpoint_store.initialize()
        
        elapsed = time.time() - start_time
        print(f"  [OK] 初始化成功（耗时: {elapsed:.2f} 秒）")
        print()
    except Exception as e:
        print(f"  [FAIL] 初始化失败: {e}")
        print(f"  - 错误类型: {type(e).__name__}")
        import traceback
        print(f"  - 详细错误:")
        traceback.print_exc()
        return False

    # 4. 验证 checkpoint_saver
    print("步骤 4: 验证 checkpoint_saver...")
    try:
        saver = checkpoint_store.get_checkpoint_saver_sync()
        if saver is None:
            print("  [FAIL] checkpoint_saver 为 None")
            return False
        print(f"  [OK] checkpoint_saver 可用")
        print(f"  - 类型: {type(saver).__name__}")
        print()
    except Exception as e:
        print(f"  [FAIL] 获取 checkpoint_saver 失败: {e}")
        return False

    # 5. 测试 Redis 连接
    print("步骤 5: 测试 Redis 连接...")
    try:
        if checkpoint_store.client is None:
            print("  [FAIL] Redis 客户端为 None")
            return False
        
        # 测试连接是否可用
        result = await checkpoint_store.client.ping()
        if result:
            print(f"  [OK] Redis 连接测试成功")
            print(f"  - PING 响应: {result}")
        else:
            print("  [FAIL] Redis PING 失败")
            return False
        
        # 测试基本操作
        test_key = "test:checkpoint:store"
        await checkpoint_store.client.set(test_key, "test_value", ex=10)
        value = await checkpoint_store.client.get(test_key)
        if value == "test_value":
            print(f"  [OK] Redis 读写测试成功")
            print(f"  - 测试键: {test_key}")
            print(f"  - 测试值: {value}")
        else:
            print("  [FAIL] Redis 读写测试失败")
            return False
        print()
    except Exception as e:
        print(f"  [FAIL] Redis 连接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 6. 测试 checkpoint saver 基本功能
    print("步骤 6: 测试 checkpoint saver 基本功能...")
    try:
        # 测试 checkpoint saver 是否可用
        # 注意：这里只测试 saver 对象是否存在，不测试实际的 checkpoint 操作
        # 因为 checkpoint 操作需要 LangGraph 的完整上下文
        saver = checkpoint_store.get_checkpoint_saver_sync()
        if saver is None:
            print("  [FAIL] checkpoint_saver 为 None")
            return False
        
        print(f"  [OK] checkpoint_saver 对象可用")
        print(f"  - 类型: {type(saver).__name__}")
        print(f"  - 方法: {[m for m in dir(saver) if not m.startswith('_')][:5]}...")
        print()
    except Exception as e:
        print(f"  [FAIL] checkpoint_saver 功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 7. 测试懒加载方法
    print("步骤 7: 测试懒加载方法...")
    try:
        # 创建一个新的 checkpoint store 实例
        new_store = RedisCheckpointStore(settings)
        
        # 测试 get_checkpoint_saver() 懒加载
        saver = await new_store.get_checkpoint_saver()
        if saver is None:
            print("  [FAIL] 懒加载返回的 checkpoint_saver 为 None")
            await new_store.close()
            return False
        
        print(f"  [OK] 懒加载方法测试成功")
        print(f"  - checkpoint_saver 类型: {type(saver).__name__}")
        
        await new_store.close()
        print()
    except Exception as e:
        print(f"  [FAIL] 懒加载方法测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 8. 清理
    print("步骤 8: 清理资源...")
    try:
        await checkpoint_store.close()
        print(f"  [OK] 资源清理成功")
        print()
    except Exception as e:
        print(f"  [WARN] 资源清理警告: {e}")
        print()

    # 总结
    print("=" * 80)
    print("[SUCCESS] 所有测试通过！RedisCheckpointStore 初始化成功。")
    print("=" * 80)
    return True


async def test_redis_checkpoint_error_handling():
    """测试错误处理场景。"""
    print("=" * 80)
    print("RedisCheckpointStore 错误处理测试")
    print("=" * 80)
    print()
    
    # 1. 测试未初始化时调用 get_checkpoint_saver_sync
    print("步骤 1: 测试未初始化时调用 get_checkpoint_saver_sync...")
    try:
        settings = Settings.from_env()
        checkpoint_store = RedisCheckpointStore(settings)
        
        try:
            saver = checkpoint_store.get_checkpoint_saver_sync()
            print("  [FAIL] 应该抛出 RuntimeError")
            return False
        except RuntimeError as e:
            if "must be initialized" in str(e):
                print(f"  [OK] 正确抛出 RuntimeError")
                print(f"  - 错误消息: {str(e)}")
            else:
                print(f"  [FAIL] RuntimeError 消息不正确: {str(e)}")
                return False
        print()
    except Exception as e:
        print(f"  [FAIL] 错误处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("=" * 80)
    print("[SUCCESS] 错误处理测试通过！")
    print("=" * 80)
    print()
    return True


async def main():
    """主函数。"""
    try:
        # 1. 测试 Redis 连接
        print("\n")
        redis_connection_success = await test_redis_connection()
        if not redis_connection_success:
            print("\n[FAIL] Redis 连接测试失败，停止后续测试")
            sys.exit(1)
        
        # 2. 测试错误处理
        print("\n")
        error_handling_success = await test_redis_checkpoint_error_handling()
        if not error_handling_success:
            print("\n[FAIL] 错误处理测试失败，停止后续测试")
            sys.exit(1)
        
        # 3. 执行主要的初始化测试
        print("\n")
        success = await test_redis_checkpoint_initialization()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Redis checkpoint 不依赖特定的事件循环类型，可以使用默认的事件循环
    asyncio.run(main())
