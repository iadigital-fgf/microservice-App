import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fgf_service.core.config import settings
from fgf_service.reports.ventas_industria.router import router as ventas_industria_router
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    logger.info("Scheduler iniciado")
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="FGF Trapani — KPI Microservice",
    description="Microservicio de KPIs financieros y operativos. Conecta Finnegans ERP con Power BI.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(ventas_industria_router, prefix="/api/v1")


@app.get("/health", tags=["Sistema"])
async def health() -> dict:
    return {"status": "ok", "env": settings.app_env}
