from sqlalchemy import select, func, update
from app.models import UserGame, User

async def update_user_total_score(user_id: int, session):
    stmt = (
        select(func.sum(UserGame.high_score))
        .where(UserGame.user_id == user_id)
    )
    result = await session.execute(stmt)
    total = result.scalar() or 0

    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(total_score=total)
    )
    await session.commit()
