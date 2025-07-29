# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc, update, insert, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import UserGame, Game, User
from app.schemas.game import Ranking, CreateGame
from app.db.session import get_async_session
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from app.models.gamesession import GameSession  # importa tu modelo
from app.schemas.gamesession import SubmitGameSession
gameRouter = APIRouter(prefix="/game", tags=["game"])

'''
async def get_game_by_name(game: str, session: AsyncSession = Depends(get_async_session)):
    query = select(Game).where(Game.name == game)
    id_exec = await session.execute(query)
    id = id_exec.scalars().first()
    return id
'''
'''
async def get_user_by_id(id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(Game).where(Game.id == id)
    result = await session.execute(query)
    return result.scalars().first()
'''

@gameRouter.post("/create-game")
async def create_game(game: CreateGame, session: AsyncSession = Depends(get_async_session)):
    exists = select(Game).where(Game.name == game.name)
    result = await session.execute(exists)
    existing_game = result.scalars().first()

    if existing_game:
        raise HTTPException(400, "Game exists")
    
    insert_stmt = insert(Game).values(name=game.name)
    await session.execute(insert_stmt)
    await session.commit()

    return {"message": "Game created"}

@gameRouter.get("")
async def get_all_games(session: AsyncSession = Depends(get_async_session)):
    select_games = select(Game)
    result = await session.execute(select_games)
    games = result.scalars().all()
    return games





def get_date_filter(period: str):
    now = datetime.utcnow()
    if period == "day":
        return now - timedelta(days=1)
    elif period == "week":
        return now - timedelta(weeks=1)
    elif period == "month":
        return now - timedelta(days=30)
    else:
        return None

@gameRouter.get("/ranking/total_score/{period}/{game_id}")
async def get_ranking(period: str, game_id:  str, session: AsyncSession = Depends(get_async_session)):

    """
    period: 'day', 'week', 'month', or 'total'
    """

    # Validación simple
    if period not in ["day", "week", "month", "total"]:
        raise HTTPException(status_code=400, detail="Invalid period. Use: day, week, month, total")
    if not game_id:
        raise HTTPException(status_code=400, detail="Game ID is required")
    if game_id == str("all"):
        stmt = (
        select(
            User.username,
            func.sum(GameSession.score).label("total_score")
        )
        .join(User, User.id == GameSession.user_id)
    )
    else:
        g_id = int(game_id)
        if g_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid Game ID")
        stmt = (
            select(
                User.username,
                func.sum(GameSession.score).label("total_score")
            )
            .join(User, User.id == GameSession.user_id)
            .join(Game, Game.id == GameSession.game_id)
            .where(Game.id == g_id)
        )
   
    # Filtrar por periodo si no es 'total'
    if period != "total":
        date_filter = get_date_filter(period)
        stmt = stmt.where(GameSession.played_at >= date_filter)

    stmt = stmt.group_by(User.id).order_by(desc("total_score")).limit(10)

    result = await session.execute(stmt)
    rows = result.all()

    return [{"username": username, "total_score": total_score} for username, total_score in rows]

@gameRouter.get("/ranking/highscore/{game_id}")
async def get_highscore_ranking(game_id: int, session: AsyncSession = Depends(get_async_session)):
    if not game_id:
        raise HTTPException(status_code=400, detail="Game ID is required")
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
async def submit_score(
    data: SubmitGameSession,
    session: AsyncSession = Depends(get_async_session)
):
    # Buscar usuario
    user_query = select(User).where(User.username == data.username)
    user_result = await session.execute(user_query)
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(404, detail="User not found")

    # Buscar juego
    game_query = select(Game).where(Game.name == data.gamename)
    game_result = await session.execute(game_query)
    game = game_result.scalars().first()

    if not game:
        raise HTTPException(404, detail="Game not found")

    # Buscar relación UserGame (después de tener user y game)
    user_game_query = select(UserGame).where(
        and_(
            UserGame.user_id == user.id,
            UserGame.game_id == game.id
        )
    )
    user_game_result = await session.execute(user_game_query)
    user_game = user_game_result.scalars().first()

    # Determinar si es highscore
    is_highscore = False
    if user_game:
        is_highscore = data.score > (user_game.highscore or 0)

        # Sumar total_score del juego
        user.total_score += data.score

        # Actualizar highscore si corresponde
        if is_highscore:
            user_game.highscore = data.score
    else:
        # Crear nueva entrada UserGame si no existe
        is_highscore = True  # primer score siempre es highscore
        user_game = UserGame(
            user_id=user.id,
            game_id=game.id,
            total_score=data.score,
            highscore=data.score
        )
        session.add(user_game)

    # Guardar nueva sesión
    insert_session = insert(GameSession).values(
        user_id=user.id,
        game_id=game.id,
        score=data.score,
        highscore=is_highscore
    )
    await session.execute(insert_session)

    # Actualizar total_score global
    user.total_score += data.score

    await session.commit()

    return {"message": "Score recorded and totals updated"}

from datetime import datetime, timedelta
from sqlalchemy import func

def get_date_range(period: str):
    now = datetime.utcnow()
    if period == "day":
        return now.replace(hour=0, minute=0, second=0, microsecond=0), now
    elif period == "week":
        start = now - timedelta(days=now.weekday())  # Monday
        return start.replace(hour=0, minute=0, second=0, microsecond=0), now
    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, now
    else:
        raise HTTPException(400, "Invalid period")

@gameRouter.get("/sessions/recent")
async def recent_sessions(limit: int = 10, session: AsyncSession = Depends(get_async_session)):
    stmt = (
        select(
            GameSession.id,
            User.username,
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
            "highscore": r.highscore
        }
        for r in rows
    ]
