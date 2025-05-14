# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.schemas.user import UserRegister, UserLogin
from app.db.session import get_async_session
from app.core.security import hash_password, verify_password
authRouter = APIRouter(prefix="/auth", tags=["auth"])

@authRouter.post("/register")
async def register_user(
    user: UserRegister,
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(User).where(User.email == user.email)
    result = await session.execute(stmt)            
    u = result.scalars().first()

    if u:
        raise HTTPException(400, "Email already registered")

    hashed_password = hash_password(user.password)
    new_user = User(
        username=user.username,
        fullname=user.fullname,
        email=user.email,
        password=hashed_password
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return {"message": "User registered successfully", "user": new_user}

@authRouter.post("/login")
async def login_user(user: UserLogin, session: AsyncSession = Depends(get_async_session)):
    stmt = select(User).where(User.email == user.email)
    result = await session.execute(stmt)
    u = result.scalars().first()

    if not u or not verify_password(user.password, u.password):
        raise HTTPException(400, "Invalid email or password")

    return {"message": "Login successful", "user": u}

@authRouter.get("/all")
async def get_all_users(session: AsyncSession = Depends(get_async_session)):
    users_query = select(User)
    result = await session.execute(users_query)
    users = result.scalars().all()
    return users
