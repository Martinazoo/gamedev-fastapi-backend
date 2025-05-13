# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import UserGame, Game, User
from app.schemas.game import Ranking
from app.db.session import get_async_session
from sqlalchemy.orm import selectinload

gameRouter = APIRouter(prefix="/game", tags=["game"])

async def get_game_by_name(game: str, session: AsyncSession = Depends(get_async_session)):
    query = select(Game).where(Game.name == game)
    id_exec = await session.execute(query)
    id = id_exec.scalars().first()
    return id

'''
async def get_user_by_id(id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(Game).where(Game.id == id)
    result = await session.execute(query)
    return result.scalars().first()
'''

@gameRouter.get("/ranking")
async def get_ranking(session: AsyncSession = Depends(get_async_session)):
    game = "Asteroids"
    game_id = await get_game_by_name(game, session)
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
            "high_score": user_game.high_score
        }
            for user_game, user in ranking
    ]

@gameRouter.post("/set-highscore")
async def set_ranking(rank: Ranking, session: AsyncSession = Depends(get_async_session)):
    user_query = select(User).where(User.username == rank.username)
    result = await session.execute(user_query)
    existing_user = result.scalars().one()

    if existing_user is None:
        raise HTTPException(400, "User does not exist")
    
    game_id = await get_game_by_name(rank.gamename, session)

    high_score_query = select(UserGame).where(UserGame.user_id == existing_user.id).where(UserGame.game_id == game_id)
    res = await session.execute(high_score_query)
    user_game_rank = res.scalars().one()

    if rank.score > user_game_rank.high_score:
        update_high_score_query = update(UserGame).where(UserGame.user_id == existing_user.id).where(UserGame.game_id == game_id).values(high_score = rank.score)
        return {"message": "High Score updated sucessfully"}


    return {"message": "Score is not higher than high_score"}