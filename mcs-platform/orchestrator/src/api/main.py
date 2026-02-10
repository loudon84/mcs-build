"""FastAPI application entry point for mcs-orchestrator."""

import os
import sys
from pathlib import Path

# CRITICAL: Windows 上必须在导入任何其他模块之前设置事件循环策略
# psycopg 不支持 ProactorEventLoop，必须使用 SelectorEventLoop
if sys.platform == "win32":
    import asyncio
    # 强制设置事件循环策略，确保后续创建的事件循环都是 SelectorEventLoop
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 确保 src/ 在 sys.path 最前，以便正确解析 api、db、internal 等包
_src_dir = Path(__file__).resolve().parent.parent  # api/main.py -> src/
_src_str = str(_src_dir.resolve())
if _src_str in sys.path:
    sys.path.remove(_src_str)
sys.path.insert(0, _src_str)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware import ExceptionMiddleware, LoggingMiddleware, RequestIdMiddleware
from api.routes.gateway import router as gateway_router
from api.routes.listener import router as listener_router
from api.routes.masterdata import router as masterdata_router
from api.routes.orchestration import router as orchestration_router
from db.engine import create_db_engine, create_session_factory
from db.repo import OrchestratorRepo
from listener.db.engine import create_listener_engine, create_listener_session_factory
from listener.repo import ListenerRepo
from internal.db.engine import create_masterdata_engine, create_masterdata_session_factory
from internal.repo import MasterDataRepo
from services.gateway_service import GatewayService
from services.listener_service import ListenerService
from services.masterdata_service import MasterDataService
from services.orchestration_service import OrchestrationService
from settings import Settings
from tools.dify_client import DifyClient
from tools.file_server import FileServerClient
from tools.mailer import Mailer

# 确保从项目根目录读取 .env 文件
# 如果从 src/ 目录运行，需要向上查找 .env
env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    os.chdir(env_file.parent)

settings = Settings.from_env()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    # Startup: Create services and start scheduler
    # Create database engines and session factories
    orchestration_engine = create_db_engine(settings)
    orchestration_session_factory = create_session_factory(orchestration_engine)
    
    masterdata_engine = create_masterdata_engine(settings)
    masterdata_session_factory = create_masterdata_session_factory(masterdata_engine)
    
    listener_engine = create_listener_engine(settings)
    listener_session_factory = create_listener_session_factory(listener_engine)
    
    # Create services
    masterdata_repo = MasterDataRepo(masterdata_session_factory())
    masterdata_service = MasterDataService(masterdata_repo, settings)
    
    gateway_service = GatewayService(settings)
    
    orchestration_repo = OrchestratorRepo(orchestration_session_factory())
    file_server = FileServerClient(settings.file_server_base_url, settings.file_server_api_key)
    dify_contract_client = DifyClient(settings.dify_base_url, settings.dify_contract_app_key)
    dify_order_client = DifyClient(settings.dify_base_url, settings.dify_order_app_key)
    mailer = Mailer(settings)
    
    orchestration_service = OrchestrationService(
        settings=settings,
        repo=orchestration_repo,
        masterdata_service=masterdata_service,
        file_server=file_server,
        dify_contract_client=dify_contract_client,
        dify_order_client=dify_order_client,
        mailer=mailer,
        gateway_service=gateway_service,
    )
    
    listener_repo = ListenerRepo(listener_session_factory())
    listener_service = ListenerService(settings, listener_repo, orchestration_service)
    
    # Store services in app.state
    app.state.masterdata_service = masterdata_service
    app.state.gateway_service = gateway_service
    app.state.orchestration_service = orchestration_service
    app.state.listener_service = listener_service
    
    # Start listener scheduler
    await listener_service.start_scheduler()
    
    yield
    
    # Shutdown: Stop scheduler and close connections
    await listener_service.stop_scheduler()


app = FastAPI(
    title="MCS Orchestrator Service",
    description="Orchestration service using LangGraph + LangServe",
    version="0.1.0",
    lifespan=lifespan,
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

app.include_router(orchestration_router)
app.include_router(gateway_router)
app.include_router(masterdata_router)
app.include_router(listener_router)


@app.get("/healthz")
async def healthz():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn 

    uvicorn.run(app, host="0.0.0.0", port=18000)

