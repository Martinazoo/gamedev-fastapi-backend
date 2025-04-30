from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserRegister
from sqlalchemy import select
from app.models import User
from app.db import get_async_session

authRouter = APIRouter()

@authRouter.post("/auth/register")
async def register_user(user: UserRegister, session: AsyncSession = Depends(get_async_session)):
    stmt = select(User).where(user.email == user.email)
    result = await session.execute(stmt)
    u = result.scalars().first()