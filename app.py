import uvicorn
import math
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import router
from storage.redis import RedisManager
from src.ratelimiter import RedisRateLimiter
from storage.mongodb import DatabaseManager

redis_manager = RedisManager()
db_manager = DatabaseManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        redis_client = await redis_manager.connect_redis()
        if redis_client is None:
            raise RuntimeError("Failed to connect to Redis")
        
        app.state.redis_manager = redis_manager
        app.state.rate_limiter = RedisRateLimiter(redis_client, max_tokens=60, refill_rate=1, interval=1)
        await db_manager.connect_and_init()
        
        yield
        
    finally:
        await redis_manager.close_redis()
        await db_manager.close_connection()

app = FastAPI(
    title="Sift API",
    description="API for Sift Search Engine",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
