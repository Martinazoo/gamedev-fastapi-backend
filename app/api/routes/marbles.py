from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, insert,  delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import MarblesDemo
from app.schemas.marbles import CreateMarbles, LeaveMarbles
from app.db.session import get_async_session

marblesRouter = APIRouter(prefix="/marbles", tags=["marbles"])

@marblesRouter.post("/join")
async def join_marbles(marble: CreateMarbles, session: AsyncSession = Depends(get_async_session)):
    stmt = select(MarblesDemo).where(MarblesDemo.username == marble.username)
    result = await session.execute(stmt)
    existing_marble = result.scalars().first()
    
    if existing_marble:
        raise HTTPException(400, "Marble already in the lobby")
    
    join_query = insert(MarblesDemo).values(color=marble.color, username=marble.username)
    await session.execute(join_query)
    await session.commit()
    
    return JSONResponse(content={"message": "Marble joined the lobby"}, status_code=201)


@marblesRouter.delete("/leave")
async def leave_marbles(marble: LeaveMarbles, session: AsyncSession  = Depends(get_async_session)):
    stmt = select(MarblesDemo).where(MarblesDemo.username == marble.username)
    result = await session.execute(stmt)
    existing_marble = result.scalars().first()

    if existing_marble is None:
        raise HTTPException(404, "Marble is not in the game")
    
    leave_query = delete(MarblesDemo).where(MarblesDemo.username == marble.username)
    await session.execute(leave_query)
    await session.commit()

    return JSONResponse(content={"message": "Marble leaved the lobby"}, status_code=201)

@marblesRouter.delete("/clear-lobby")
async def clear_marbles_lobby(session: AsyncSession = Depends(get_async_session)):
    clear_query = delete(MarblesDemo)
    await session.execute(clear_query)
    await session.commit()
    return JSONResponse(content={"message": "All marbles cleared from the lobby"}, status_code=200)

@marblesRouter.get("/all")
async def get_all_marbles(session: AsyncSession = Depends(get_async_session)):
    get_all_query = select(MarblesDemo)
    result = await session.execute(get_all_query)
    marbles = result.scalars().all()
    return marbles