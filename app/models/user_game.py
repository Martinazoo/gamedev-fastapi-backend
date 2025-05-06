from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer
from app.db.base import Base
from app.models.user import User
from app.models.game import Game
class UserGame(Base):
    __tablename__ = "users_games"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), primary_key=True)
    time_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relaciones a User y Game
    user: Mapped[User] = relationship(
        "User",
        back_populates="games_played"
    )
    game: Mapped["Game"] = relationship(
        "Game",
        back_populates="users"
    )
