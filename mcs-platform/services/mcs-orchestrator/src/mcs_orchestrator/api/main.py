"""FastAPI application entry point for mcs-orchestrator."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mcs_orchestrator.api.middleware import ExceptionMiddleware, LoggingMiddleware, RequestIdMiddleware
from mcs_orchestrator.api.routes import router
from mcs_orchestrator.settings import Settings

settings = Settings.from_env()

app = FastAPI(
    title="MCS Orchestrator Service",
    description="Orchestration service using LangGraph + LangServe",
    version="0.1.0",
)

# Add middleware
app.add_middleware(RequestIdMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ExceptionMiddleware)

# CORS (if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/healthz")
async def healthz():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

