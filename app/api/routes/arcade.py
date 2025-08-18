from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid

from app.db.session import get_async_session
from app.models import ArcadeSession, User
from app.core.security import get_current_user

arcadeRouter = APIRouter(prefix="/arcade", tags=["arcade"])


# 📌 Modelo de request para vincular sesión
class LinkSessionRequest(BaseModel):
    session_id: str


# Crear una nueva sesión arcade (sin usuario todavía)
@arcadeRouter.post("/create-session")
async def create_session(session: AsyncSession = Depends(get_async_session)):
    session_id = str(uuid.uuid4())
    new_session = ArcadeSession(id=session_id, is_authenticated=False, user_id=None)
    session.add(new_session)
    await session.commit()
    return {"session_id": session_id}


# Vincular sesión arcade con el usuario logeado
@arcadeRouter.post("/link-session")
async def link_session(
    data: LinkSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(select(ArcadeSession).where(ArcadeSession.id == data.session_id))
    arcade_session = result.scalars().first()

    if not arcade_session:
        raise HTTPException(status_code=404, detail="Session not found")

    arcade_session.user_id = current_user.id
    arcade_session.is_authenticated = True
    await db.commit()
    await db.refresh(arcade_session)

    return {"message": "Arcade linked", "user": current_user.username}


from sqlalchemy.orm import selectinload

@arcadeRouter.get("/status")
async def check_status(session_id: str, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(
        select(ArcadeSession)
        .options(selectinload(ArcadeSession.user))  # 👈 esto carga el user de forma async
        .where(ArcadeSession.id == session_id)
    )
    arcade_session = result.scalars().first()

    if not arcade_session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "is_authenticated": arcade_session.is_authenticated,
        "user": arcade_session.user.username if arcade_session.user else None
    }
