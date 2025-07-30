from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc, update, insert, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from app.models import UserGame, Game, User
from app.schemas.game import Ranking, CreateGame
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
    query = (
        select(User.username, UserGame.highscore)
        .join(User, User.id == UserGame.user_id)
        .where(UserGame.game_id == game_id)
        .order_by(desc(UserGame.highscore))
        .limit(10)
    )
    result = await session.execute(query)
    return [{"username": r.username, "highscore": r.highscore} for r in result.all()]


@gameRouter.post("/submit-score")
async def submit_score(data: SubmitGameSession, session: AsyncSession = Depends(get_async_session)):
    user_q = await session.execute(select(User).where(User.username == data.username))
    user = user_q.scalars().first()
    if not user:
        raise HTTPException(404, "User not found")

    game_q = await session.execute(select(Game).where(Game.name == data.gamename))
    game = game_q.scalars().first()
    if not game:
        raise HTTPException(404, "Game not found")

    user_game_q = await session.execute(select(UserGame).where(
        and_(UserGame.user_id == user.id, UserGame.game_id == game.id)
    ))
    user_game = user_game_q.scalars().first()

    is_highscore = False
    if user_game:
        is_highscore = data.score > (user_game.highscore or 0)
        user.total_score += data.score
        if is_highscore:
            user_game.highscore = data.score
    else:
        is_highscore = True
        user_game = UserGame(
            user_id=user.id,
            game_id=game.id,
            total_score=data.score,
            highscore=data.score
        )
        session.add(user_game)

    await session.execute(insert(GameSession).values(
        user_id=user.id,
        game_id=game.id,
        score=data.score,
        highscore=is_highscore,
        played_at=datetime.utcnow()
    ))

    user.total_score += data.score
    await session.commit()
    return {"message": "Score recorded and totals updated"}


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
