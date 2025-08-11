from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc, insert, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from app.models import Game, User
from app.schemas.game import CreateGame
from app.schemas.gamesession import SubmitGameSession
from app.db.session import get_async_session
from app.models.gamesession import GameSession
from datetime import datetime, timedelta

gameRouter = APIRouter(prefix="/game", tags=["game"])


@gameRouter.get("/get-game-by-name/{game}")
async def get_game_by_name(game: str, session: AsyncSession = Depends(get_async_session)):
    query = select(Game).where(Game.name == game)
    result = await session.execute(query)
    return result.scalars().first()


@gameRouter.get("/get-game-by-id/{id}")
async def get_game_by_id(id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(Game).where(Game.id == id)
    result = await session.execute(query)
    return result.scalars().first()


@gameRouter.post("/create-game")
async def create_game(game: CreateGame, session: AsyncSession = Depends(get_async_session)):
    exists = select(Game).where(Game.name == game.name)
    result = await session.execute(exists)
    existing_game = result.scalars().first()

    if existing_game:
        raise HTTPException(400, "Game already exists")

    insert_stmt = insert(Game).values(name=game.name)
    await session.execute(insert_stmt)
    await session.commit()
    return {"message": "Game created successfully"}


@gameRouter.get("")
async def get_all_games(session: AsyncSession = Depends(get_async_session)):
    query = select(Game)
    result = await session.execute(query)
    return result.scalars().all()


def get_date_filter(period: str):
    now = datetime.utcnow()
    if period == "day":
        return now - timedelta(days=1)
    elif period == "week":
        return now - timedelta(weeks=1)
    elif period == "month":
        return now - timedelta(days=30)
    return None


@gameRouter.get("/ranking/total_score/{period}/{game_id}")
async def get_total_score_ranking(period: str, game_id: str, session: AsyncSession = Depends(get_async_session)):
    if period not in ["day", "week", "month", "total"]:
        raise HTTPException(400, "Invalid period")

    stmt = select(
        User.username,
        func.sum(GameSession.score).label("total_score")
    ).join(User, User.id == GameSession.user_id)

    if game_id != "all":
        stmt = stmt.where(GameSession.game_id == int(game_id))

    if period != "total":
        date_filter = get_date_filter(period)
        stmt = stmt.where(GameSession.played_at >= date_filter)

    stmt = stmt.group_by(User.id).order_by(desc("total_score")).limit(10)
    result = await session.execute(stmt)
    rows = result.all()

    return [{"username": r.username, "total_score": r.total_score} for r in rows]


@gameRouter.get("/ranking/highscore/{game_id}")
async def get_highscore_ranking(game_id: int, session: AsyncSession = Depends(get_async_session)):
    stmt = (
        select(
            User.username,
            func.max(GameSession.score).label("highscore")
        )
        .join(GameSession, GameSession.user_id == User.id)
        .where(GameSession.game_id == game_id)
        .group_by(User.id)
        .order_by(desc("highscore"))
        .limit(10)
    )
    result = await session.execute(stmt)
    return [{"username": r.username, "highscore": r.highscore} for r in result.all()]


@gameRouter.post("/submit-score")
async def submit_score(data: SubmitGameSession, session: AsyncSession = Depends(get_async_session)):
    # Obtener usuario
    user_q = await session.execute(select(User).where(User.username == data.username))
    user = user_q.scalars().first()
    if not user:
        raise HTTPException(404, "User not found")

    # Obtener juego
    game_q = await session.execute(select(Game).where(Game.name == data.gamename))
    game = game_q.scalars().first()
    if not game:
        raise HTTPException(404, "Game not found")

    # Verificar si este score es highscore
    highscore_q = await session.execute(
        select(func.max(GameSession.score))
        .where(
            GameSession.user_id == user.id,
            GameSession.game_id == game.id
        )
    )
    max_score = highscore_q.scalar()
    is_highscore = data.score > (max_score or 0)

    # Insertar nueva sesión
    await session.execute(insert(GameSession).values(
        user_id=user.id,
        game_id=game.id,
        score=data.score,
        time_played=data.time_played,
        highscore=is_highscore,
        played_at=datetime.utcnow()
    ))

    await session.commit()
    return {"message": "Score recorded", "highscore": is_highscore}


@gameRouter.get("/sessions/recent")
async def recent_sessions(limit: int = 10, session: AsyncSession = Depends(get_async_session)):
    stmt = (
        select(
            GameSession.id,
            User.username,
            User.profile_image,
            Game.name.label("game_name"),
            GameSession.score,
            GameSession.played_at,
            GameSession.highscore
        )
        .join(User, User.id == GameSession.user_id)
        .join(Game, Game.id == GameSession.game_id)
        .order_by(desc(GameSession.played_at))
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.all()
    return [
        {
            "id": r.id,
            "username": r.username,
            "game": r.game_name,
            "score": r.score,
            "played_at": r.played_at,
            "highscore": r.highscore,
            "profile_image": r.profile_image 
        }
        for r in rows
    ]
