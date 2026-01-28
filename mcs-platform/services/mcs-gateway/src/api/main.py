"""FastAPI application entry point for mcs-gateway."""

from fastapi import FastAPI

from api.routes import router
from settings import Settings

settings = Settings.from_env()

app = FastAPI(
    title="MCS Gateway Service",
    description="External systems integration gateway (ERP, etc.)",
    version="0.1.0",
)

app.include_router(router)


@app.get("/healthz")
async def healthz():
    """Health check endpoint."""
    return {"status": "ok", "service": "mcs-gateway"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)

