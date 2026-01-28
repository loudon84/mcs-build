"""FastAPI application entry point for mcs-masterdata."""

from fastapi import FastAPI

from api.routes import router
from settings import Settings

settings = Settings.from_env()

app = FastAPI(
    title="MCS Master Data Service",
    description="Master data management service for MCS Platform",
    version="0.1.0",
)

app.include_router(router)


@app.get("/healthz")
async def healthz():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)

