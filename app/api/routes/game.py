# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc, update, insert, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import UserGame, Game, User
from app.schemas.game import Ranking, CreateGame
from app.db.session import get_async_session
from sqlalchemy.orm import selectinload

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
            "high_score": user_game.high_score
        }
            for user_game, user in ranking
    ]


@gameRouter.post("/set-highscore")
async def set_ranking(rank: Ranking, session: AsyncSession = Depends(get_async_session)):
    user_query = select(User).where(User.username == rank.username)
    result = await session.execute(user_query)
    existing_user = result.scalars().first()

    if existing_user is None:
        raise HTTPException(400, "User does not exist")
    
    query_gameid = select(Game).where(Game.name == rank.gamename)
    id_exec = await session.execute(query_gameid)
    game = id_exec.scalars().first()

    if game is None:
        raise HTTPException(400, "Game does not exist")
    
    game_id = game.id

    high_score_query = select(UserGame).where(
        and_(
            UserGame.user_id == existing_user.id,
            UserGame.game_id == game_id
        )
    )
    res = await session.execute(high_score_query)
    a_high_score = res.scalars().first()

    if a_high_score is None:
        insert_query = insert(UserGame).values(
            user_id=existing_user.id,
            game_id=game_id,
            high_score=rank.score
        )
        await session.execute(insert_query)
        await session.commit()
        return {"message": "High Score created successfully"}
    
    if rank.score > a_high_score.high_score:
        update_high_score_query = update(UserGame).where(
            and_(
                UserGame.user_id == existing_user.id,
                UserGame.game_id == game_id
            )
        ).values(high_score=rank.score)
        await session.execute(update_high_score_query)
        await session.commit()
        return {"message": "High Score updated successfully"}

    return {"message": "Score is not higher than current high score"}


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

@gameRouter.get("/all")
async def get_all_games(session: AsyncSession = Depends(get_async_session)):
    select_games = select(Game)
    result = await session.execute(select_games)
    games = result.scalars().all()
    return games