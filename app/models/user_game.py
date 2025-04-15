from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from app.db.base import Base
class UserGame(Base):
    __tablename__ = "users_games"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), primary_key=True)
    time_played: Mapped[int] = mapped_column(nullable=False, default=0)  

    user: Mapped["User"] = relationship("User", back_populates="games")# type: ignore
    game: Mapped["Game"] = relationship("Game", back_populates="users")# type: ignore
    
    