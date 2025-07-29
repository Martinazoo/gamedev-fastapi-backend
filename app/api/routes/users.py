from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.db.session import get_async_session
from app.schemas.user import UserPublic
from typing import List

usersRouter = APIRouter(prefix="/users", tags=["users"])


@usersRouter.get("/", response_model=List[UserPublic])
async def get_users(
    session: AsyncSession = Depends(get_async_session),
    limit: int = Query(default=50, ge=1),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    search: str = Query(default=None),
):
    stmt = select(User)

    if search:
        stmt = stmt.where(User.username.ilike(f"%{search}%"))

    if order == "asc":
        stmt = stmt.order_by(User.total_score.asc())
    else:
        stmt = stmt.order_by(User.total_score.desc())

    stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    users = result.scalars().all()
    return users


@usersRouter.get("/{username}", response_model=UserPublic)
async def get_user_by_username(
    username: str,
    session: AsyncSession = Depends(get_async_session)
):
    stmt = select(User).where(User.username == username)
    result = await session.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
