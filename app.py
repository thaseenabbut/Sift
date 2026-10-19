import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.api.routes import router
from storage.mongodb import db_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_manager.connect_and_init()
    try:
        yield
    finally:
        await db_manager.close()

app = FastAPI(
    title="Sift API",
    description="API for Sift Search Engine",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
