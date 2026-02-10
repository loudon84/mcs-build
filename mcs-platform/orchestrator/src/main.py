"""Main entry point for MCS Orchestrator service."""

import os
import sys
from pathlib import Path

# CRITICAL: Windows 上必须在导入任何其他模块之前设置事件循环策略
# psycopg 不支持 ProactorEventLoop，必须使用 SelectorEventLoop
if sys.platform == "win32":
    import asyncio
    # 强制设置事件循环策略，确保后续创建的事件循环都是 SelectorEventLoop
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 确保 src/ 目录在 Python 路径最前，避免 masterdata/api 等包被其他路径下的同名模块遮蔽
_current_file = Path(__file__).resolve()
_src_dir = _current_file.parent.resolve()  # src/ 目录（绝对路径）
_src_str = str(_src_dir)
if _src_str in sys.path:
    sys.path.remove(_src_str)
sys.path.insert(0, _src_str)

# 确保从项目根目录读取 .env 文件
_env_file = _current_file.parent.parent / ".env"
if _env_file.exists():
    os.chdir(_env_file.parent)


def setup_event_loop():
    """Setup correct event loop policy for Windows compatibility with psycopg.
    
    psycopg 在 Windows 上不能使用 ProactorEventLoop，必须使用 SelectorEventLoop。
    通过设置事件循环策略，确保 uvicorn 创建的事件循环是 SelectorEventLoop。
    """
    import asyncio
    import sys
    
    if sys.platform == "win32":
        # 设置事件循环策略为 WindowsSelectorEventLoopPolicy
        # 这样 uvicorn 创建的事件循环就会是 SelectorEventLoop 而不是 ProactorEventLoop
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def main():
    """Main entry point for starting the orchestrator service."""
    # 在导入任何异步代码之前设置正确的事件循环
    setup_event_loop()
    
    import uvicorn

    # 导入 FastAPI 应用（这会触发所有初始化逻辑）
    from api.main import app

    # 从环境变量或默认值获取配置（PORT 冲突时可设 PORT=18001 等）
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "18100"))
    log_level = os.getenv("LOG_LEVEL", "info")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        loop="asyncio",  # 明确指定使用 asyncio 事件循环
    )


if __name__ == "__main__":
    main()
