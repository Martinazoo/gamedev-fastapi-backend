from fastapi import APIRouter, Depends, HTTPException

authRouter = APIRouter()

@authRouter.post("/auth/register")
async def register_user(user: UserRegister):