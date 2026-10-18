from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Hello World"}