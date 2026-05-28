import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.base import init_db
from app.scheduler import scheduler, setup_jobs
from app.api import signals, briefs, competitors, trade_shows, trigger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Bisdom Market Intelligence Platform...")
    init_db(settings.DATABASE_URL)
    setup_jobs()
    scheduler.start()
    logger.info("Scheduler started with %d jobs.", len(scheduler.get_jobs()))
    yield
    logger.info("Shutting down...")
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Bisdom Market Intelligence API",
    description="Collects market signals and delivers daily intelligence briefs for Bisdom.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(signals.router)
app.include_router(briefs.router)
app.include_router(competitors.router)
app.include_router(trade_shows.router)
app.include_router(trigger.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "bisdom-intelligence"}
