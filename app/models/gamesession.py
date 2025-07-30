from sqlalchemy import DateTime, func, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

from sqlalchemy import Boolean

class GameSession(Base):
    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    highscore: Mapped[bool] = mapped_column(Boolean, default=False)
    played_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now())

    user = relationship("User", backref="game_sessions")
    game = relationship("Game", backref="game_sessions")
