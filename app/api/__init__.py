from fastapi import APIRouter
from app.api.routes import authRouter

api_router = APIRouter()
api_router.include_router(authRouter, prefix="/auth", tags=["auth"])
#api_router.include_router(user.router, prefix="/users", tags=["users"])
