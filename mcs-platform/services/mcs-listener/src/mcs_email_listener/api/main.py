"""FastAPI application entry point for mcs-email-listener."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from mcs_email_listener.api.routes import router
from mcs_email_listener.scheduler import EmailScheduler
from mcs_email_listener.settings import Settings

settings = Settings.from_env()
scheduler: EmailScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    global scheduler
    scheduler = EmailScheduler(settings)
    await scheduler.start()

    yield

    # Shutdown
    if scheduler:
        await scheduler.stop()


app = FastAPI(
    title="MCS Email Listener Service",
    description="Email listening and fetching service",
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

