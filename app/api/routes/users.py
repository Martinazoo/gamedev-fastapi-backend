from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from app.models import User
from app.db.session import get_async_session
from app.models.game import Game
from app.models.user_game import UserGame
from app.schemas.user import AvatarUpdate, UserPublic
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


@usersRouter.patch("/avatar")
async def update_avatar(
    avatar: AvatarUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    stmt = (
        update(User)
        .where(User.id == current_user.id)
        .values(profile_image=str(avatar.profile_image))
    )
    
    await session.execute(stmt)
    await session.commit()
    return {"message": "Avatar updated", "profile_image": avatar.profile_image}


@usersRouter.get("/user-profile/{username}")
async def get_user_profile(
    username: str,
    session: AsyncSession = Depends(get_async_session)
):
    # 1. Obtener el usuario
    user_query = select(User).where(User.username == username)
    user_result = await session.execute(user_query)
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Obtener juegos jugados
    user_games_query = (
        select(UserGame, Game)
        .join(Game, UserGame.game_id == Game.id)
        .where(UserGame.user_id == user.id)
    )
    result = await session.execute(user_games_query)
    user_games = result.all()

    games_played = []
    total_score = 0
    total_play_time = 0

    for user_game, game in user_games:
        max_score = user_game.highscore
        time_played = user_game.time_played if hasattr(user_game, "time_played") else 0

        games_played.append({
            "gameName": game.name,
            "maxScore": max_score,
            "timePlayed": time_played
        })

        total_score += max_score
        total_play_time += time_played

    # 3. Parsear nombre completo si es necesario
    fullname_parts = (user.fullname or "").split(" ")
    first_name = fullname_parts[0] if fullname_parts else ""
    last_name = " ".join(fullname_parts[1:]) if len(fullname_parts) > 1 else ""

    return {
        "username": user.username,
        "firstName": first_name,
        "lastName": last_name,
        "email": user.email,
        "profilePicture": user.profile_image,
        "gamesPlayed": games_played,
        "total_score": total_score
    }
