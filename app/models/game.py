# app/models/game.py
from typing import List
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base

class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relación inversa con UserGame
    users: Mapped[List["UserGame"]] = relationship(
        "UserGame",
        back_populates="game",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"Game(id={self.id!r}, name={self.name!r})"
