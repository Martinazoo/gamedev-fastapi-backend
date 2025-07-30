# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc, update, insert, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from app.models import UserGame, Game, User
from app.schemas.game import Ranking, CreateGame
from app.db.session import get_async_session
from sqlalchemy.orm import selectinload
<<<<<<< HEAD
from app.core.user_games import update_user_total_score
=======
from datetime import datetime, timedelta
from app.models.gamesession import GameSession  # importa tu modelo
from app.schemas.gamesession import SubmitGameSession
>>>>>>> ivan
gameRouter = APIRouter(prefix="/game", tags=["game"])

@gameRouter.get("/get-game-by-name/{game}")
async def get_game_by_name(game: str, session: AsyncSession = Depends(get_async_session)):
    query = select(Game).where(Game.name == game)
    id_exec = await session.execute(query)
    id = id_exec.scalars().first()
    return id

@gameRouter.get("/get-game-by-id/{id}")
async def get_game_by_id(id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(Game).where(Game.id == id)
    result = await session.execute(query)
    return result.scalars().first()


<<<<<<< HEAD
@gameRouter.get("/ranking")
async def get_ranking(session: AsyncSession = Depends(get_async_session)):
    game = "Asteroids"
    query_gameid = select(Game).where(Game.name == game)
    id_exec = await session.execute(query_gameid)
    game_id = id_exec.scalars().first().id
    print("IDDDDDDDDDDDDDDDDDDD")
    print(game_id)
    top_query = (
    select(UserGame, User)
    .join(User, User.id == UserGame.user_id)
    .where(UserGame.game_id == game_id)
    .order_by(desc(UserGame.high_score))
    .limit(5)
)
    result = await session.execute(top_query)
    ranking = result.all()
    
    return [
        {
            "username": user.username,
            "high_score": user_game.high_score,
            "profile_image": user.profile_image,
            "total_score": user.total_score
        }
            for user_game, user in ranking
    ]


@gameRouter.post("/highscore")
async def set_ranking(rank: Ranking, session: AsyncSession = Depends(get_async_session)):
    user_query = select(User).where(User.username == rank.username)
    result = await session.execute(user_query)
    existing_user = result.scalars().first()

    if not existing_user:
        raise HTTPException(400, "User does not exist")
    
    query_gameid = select(Game).where(Game.name == rank.gamename)
    id_exec = await session.execute(query_gameid)
    game = id_exec.scalars().first()

    if not game:
        raise HTTPException(400, "Game does not exist")

    game_id = game.id
    user_id = existing_user.id

    high_score_query = select(UserGame).where(
        and_(UserGame.user_id == user_id, UserGame.game_id == game_id)
    )
    res = await session.execute(high_score_query)
    a_high_score = res.scalars().first()

    if a_high_score is None:
        insert_query = insert(UserGame).values(
            user_id=user_id,
            game_id=game_id,
            high_score=rank.score
        )
        await session.execute(insert_query)
        await update_user_total_score(user_id, session)
        return {"message": "High Score created successfully"}
    
    if rank.score > a_high_score.high_score:
        update_high_score_query = (
            update(UserGame)
            .where(
                and_(
                    UserGame.user_id == user_id,
                    UserGame.game_id == game_id
                )
            )
            .values(high_score=rank.score)
        )
        await session.execute(update_high_score_query)
        await update_user_total_score(user_id, session)
        return {"message": "High Score updated successfully"}

    return {"message": "Score is not higher than current high score"}



@gameRouter.post("/game")
=======
@gameRouter.post("/create-game")
>>>>>>> ivan
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

<<<<<<< HEAD
@gameRouter.get("/get-all-games-from-current-user")
async def get_all_games_from_current_user(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    username = current_user.username
    # Obtener el usuario primero
    user_query = select(User).where(User.username == username)
    user_result = await session.execute(user_query)
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Obtener los juegos jugados por ese usuario junto con su información
    user_games_query = (
        select(UserGame, Game)
        .join(Game, UserGame.game_id == Game.id)
        .where(UserGame.user_id == user.id)
    )
    result = await session.execute(user_games_query)
    user_games = result.all()

    if not user_games:
        raise HTTPException(status_code=404, detail="No games found for this user")

    return [
        {
            "game_name": game.name,
            "high_score": user_game.high_score,
            "game_id": game.id
        }
        for user_game, game in user_games
    ]


@gameRouter.get("/get-all-games-from-user/{username}")
async def get_all_games_from_user(
    username: str,
    session: AsyncSession = Depends(get_async_session)
):
    # Obtener el usuario primero
    user_query = select(User).where(User.username == username)
=======




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
>>>>>>> ivan
    user_result = await session.execute(user_query)
    user = user_result.scalars().first()

    if not user:
<<<<<<< HEAD
        raise HTTPException(status_code=404, detail="User not found")

    # Obtener los juegos jugados por ese usuario junto con su información
    user_games_query = (
        select(UserGame, Game)
        .join(Game, UserGame.game_id == Game.id)
        .where(UserGame.user_id == user.id)
    )
    result = await session.execute(user_games_query)
    user_games = result.all()

    if not user_games:
        raise HTTPException(status_code=404, detail="No games found for this user")

    return [
        {
            "game_name": game.name,
            "high_score": user_game.high_score,
            "game_id": game.id
        }
        for user_game, game in user_games
=======
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
>>>>>>> ivan
    ]
