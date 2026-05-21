from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import state
from services.background import repeatInsert
import os
import logging
from socket_handlers.web_socket import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

origins = [
    "*",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    await state.db.connect()
    logger.info("Starting on port: %s", os.environ.get("PORT", "NOT SET"))

    logger.info("Database connected successfully")

    time1 = datetime.now()
    task = asyncio.create_task(repeatInsert())
    time2 = datetime.now()
    diff = time2 - time1
    logger.info("Background task created in %d.%06ds", diff.seconds, diff.microseconds)
    print("🔥 MAIN.PY IS RUNNING")
    print("🔥 ROUTES:", [r.path for r in app.routes])
    await asyncio.sleep(0) 
    logger.info("Background task registered: %s", task)
    task.add_done_callback(lambda t: logger.error("Background task ended — exception: %s", t.exception()) if not t.cancelled() else logger.warning("Background task was cancelled"))
    yield
    await state.db.closeConnection()
    await state.ws.closeConnections()
    logger.info("Database connection closed and WebSocket connections cleaned up")

app = FastAPI(lifespan=lifespan)
app.state.limiter = state.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include WebSocket routers
app.include_router(router)

print("🔥 MAIN.PY IS RUNNING")
print("🔥 ROUTES:", [r.path for r in app.routes])
