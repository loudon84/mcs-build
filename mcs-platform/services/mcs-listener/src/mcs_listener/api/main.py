"""FastAPI application entry point for mcs-listener."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from mcs_listener.api.routes import router
from mcs_listener.db.engine import create_db_engine, create_session_factory
from mcs_listener.db.repo import ListenerRepo
from mcs_listener.scheduler import UnifiedScheduler
from mcs_listener.settings import Settings

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

