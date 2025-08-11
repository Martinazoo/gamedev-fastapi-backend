# app/models/game_session.py
from sqlalchemy import DateTime, func, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class GameSession(Base):
    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    highscore: Mapped[bool] = mapped_column(Boolean, default=False)
    played_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now())
    time_played: Mapped[int] = mapped_column(Integer, nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="game_sessions")
    game: Mapped["Game"] = relationship("Game", back_populates="game_sessions")
