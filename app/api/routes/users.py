from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password, validate_password, get_current_user  # Asumiendo que la tienes ya

from app.models import *
from app.db.session import get_async_session
from app.schemas.user import AvatarUpdate, UserPublic, UserRead, UserUpdate
from typing import List

usersRouter = APIRouter(prefix="/users", tags=["users"])


@usersRouter.get("/", response_model=List[UserPublic])
async def get_users(
    session: AsyncSession = Depends(get_async_session),
    limit: int = Query(default=50, ge=1),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    search: str = Query(default=None),
):
    # Subquery: calcular total_score por usuario
    score_subq = (
        select(
            GameSession.user_id,
            func.coalesce(func.sum(GameSession.score), 0).label("total_score")
        )
        .group_by(GameSession.user_id)
        .subquery()
    )

    # Select usuarios + total_score
    stmt = (
        select(User, score_subq.c.total_score)
        .outerjoin(score_subq, User.id == score_subq.c.user_id)
    )

    if search:
        stmt = stmt.where(User.username.ilike(f"%{search}%"))

    if order == "asc":
        stmt = stmt.order_by(score_subq.c.total_score.asc().nullsfirst())
    else:
        stmt = stmt.order_by(score_subq.c.total_score.desc().nullslast())

    stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    users_with_score = result.all()

    # Serializar respuesta
    response = []
    for user, total_score in users_with_score:
        user_dict = UserPublic.model_validate(user).dict()
        user_dict["total_score"] = total_score or 0
        response.append(user_dict)

    return response


@usersRouter.get("/{username}", response_model=UserPublic)
async def get_user_by_username(
    username: str,
    session: AsyncSession = Depends(get_async_session)
):
    # Subquery: calcular total_score del usuario
    score_subq = (
        select(
            GameSession.user_id,
            func.coalesce(func.sum(GameSession.score), 0).label("total_score")
        )
        .group_by(GameSession.user_id)
        .subquery()
    )

    stmt = (
        select(User, score_subq.c.total_score)
        .outerjoin(score_subq, User.id == score_subq.c.user_id)
        .where(User.username == username)
    )

    result = await session.execute(stmt)
    user_with_score = result.first()

    if not user_with_score:
        raise HTTPException(status_code=404, detail="User not found")

    user, total_score = user_with_score
    user_dict = UserPublic.model_validate(user).dict()
    user_dict["total_score"] = total_score or 0

    return user_dict


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

@usersRouter.delete("/avatar")
async def delete_avatar(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    stmt = (
        update(User)
        .where(User.id == current_user.id)
        .values(profile_image=None)
    )

    await session.execute(stmt)
    await session.commit()
    return {"message": "Avatar deleted"}

    st

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

    # 2. Obtener los juegos jugados por el usuario
    games_query = (
        select(Game.id, Game.name)
        .join(GameSession, Game.id == GameSession.game_id)
        .where(GameSession.user_id == user.id)
        .distinct()
    )
    games_result = await session.execute(games_query)
    games = games_result.all()

    games_played = []
    total_score = 0
    for game_id, game_name in games:
        # Obtener el highscore de ese juego (mayor score registrado)
        highscore_query = (
            select(func.max(GameSession.score))
            .where(
                GameSession.user_id == user.id,
                GameSession.game_id == game_id,
            )
        )
        highscore_result = await session.execute(highscore_query)
        highscore = highscore_result.scalar() or 0

        # Sumar todos los scores de ese juego para total parcial
        total_score_query = (
            select(func.coalesce(func.sum(GameSession.score), 0))
            .where(
                GameSession.user_id == user.id,
                GameSession.game_id == game_id,
            )
        )
        total_score_result = await session.execute(total_score_query)
        total_score_game = total_score_result.scalar() or 0

        # Obtener el tiempo total jugado de ese juego
        total_time_played_query = (
            select(func.coalesce(func.sum(GameSession.time_played), 0))
            .where(
                GameSession.user_id == user.id,
                GameSession.game_id == game_id,
            )
        )
        total_time_played_result = await session.execute(total_time_played_query)
        total_time_played = total_time_played_result.scalar() or 0

        games_played.append({
            "gameName": game_name,
            "maxScore": highscore,
            "totalTimePlayed": total_time_played,
            "totalScore": total_score_game
        })

        total_score += total_score_game

    # 3. Parsear nombre completo
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


@usersRouter.put("/update-profile")
async def update_profile(
    profile: UserUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    # Verificar username duplicado
    if profile.username:
        result = await session.execute(
            select(User).where(
                User.username == profile.username,
                User.id != current_user.id
            )
        )
        existing_username = result.scalar_one_or_none()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This username is already taken."
            )

    # Verificar email duplicado
    if profile.email:
        result = await session.execute(
            select(User).where(
                User.email == profile.email,
                User.id != current_user.id
            )
        )
        existing_email = result.scalar_one_or_none()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already taken"
            )

    # Validar contraseña si el usuario quiere cambiarla
    values_to_update = {}
    if profile.username:
        values_to_update["username"] = profile.username
    if profile.fullname:
        values_to_update["fullname"] = profile.fullname
    if profile.email:
        values_to_update["email"] = profile.email
    if profile.password:
        validate_password(profile.password)
        values_to_update["password"] = hash_password(profile.password)

    if not values_to_update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update."
        )

    stmt = (
        update(User)
        .where(User.id == current_user.id)
        .values(**values_to_update)
    )

    await session.execute(stmt)
    await session.commit()
    
    return {"message": "Profile updated"}