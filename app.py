import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from storage.redis import RedisManager
from storage.mongodb import db_manager

redis_manager = RedisManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await redis_manager.connect_redis()
        await db_manager.connect_and_init()
        
        yield
        
    finally:
        await redis_manager.close_redis()
        await db_manager.close()

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
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
