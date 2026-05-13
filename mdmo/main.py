import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from mdmo.database import init_db
from mdmo.scheduler import init_scheduler, scan_launchpad

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    init_scheduler()
    asyncio.ensure_future(scan_launchpad())
    logger.info("MDMO server started")
    yield
    logger.info("MDMO server shutting down")


app = FastAPI(title="MDMO - Ubuntu Package Hygiene Dashboard", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="mdmo/static"), name="static")

from mdmo.api.router import router as api_router

app.include_router(api_router)
