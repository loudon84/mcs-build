"""FastAPI application entry point for mcs-listener."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from api.routes import router
from db.engine import create_db_engine, create_session_factory
from db.repo import ListenerRepo
from scheduler import UnifiedScheduler
from settings import Settings

# 确保从项目根目录读取 .env 文件
# 如果从 src/ 目录运行，需要向上查找 .env
env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    os.chdir(env_file.parent)

settings = Settings.from_env()
scheduler: UnifiedScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    global scheduler
    
    # Initialize database
    engine = create_db_engine(settings)
    session_factory = create_session_factory(engine)
    repo = ListenerRepo(session_factory())
    
    scheduler = UnifiedScheduler(settings, repo=repo)
    await scheduler.start()

    yield

    # Shutdown
    if scheduler:
        await scheduler.stop()


app = FastAPI(
    title="MCS Listener Service",
    description="Multi-channel communication listener service (Email, WeChat, etc.)",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/healthz")
async def healthz():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)

