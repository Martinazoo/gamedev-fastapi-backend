# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.schemas.user import UserRegister, UserLogin
from app.db.session import get_async_session

authRouter = APIRouter(prefix="/auth", tags=["auth"])

@authRouter.post("/register")
async def register_user(
    user: UserRegister,
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(User).where(User.email == user.email)
    result = await session.execute(stmt)            # ahora session es AsyncSession
    u = result.scalars().first()

    if u:
        raise HTTPException(400, "Email already registered")

    new_user = User(
        username=user.username,
        fullname=user.fullname,
        email=user.email,
        password=user.password
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return {"message": "User registered successfully", "user": new_user}

@authRouter.post("/login")
async def login_user(
    user: UserLogin,
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(User).where(User.email == user.email)
    result = await session.execute(stmt)
    u = result.scalars().first()

    if not u or u.password != user.password:
        raise HTTPException(400, "Invalid email or password")

    return {"message": "Login successful", "user": u}
