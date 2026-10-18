import uvicorn
from src.api.routes import router
from fastapi import FastAPI

app = FastAPI(
    title="Sift API",
    description="API for Sift Search Engine",
    version="0.1.0",
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
