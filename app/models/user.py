from sqlalchemy import Column, Integer, Table, String, ForeignKey
from app.db.base import Base
from sqlalchemy.orm import relationship, Mapped, mapped_column, relationship
from typing import Optional, List
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False, autoincrement=True)
    username: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    fullname: Mapped[str] = mapped_column(String(40), nullable=False)
    email: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    profile_image: Mapped[str] = mapped_column(nullable=True) 
    total_score: Mapped[int] = mapped_column(nullable=False)
    games_played: Mapped[List["UserGame"]] = relationship( # type: ignore
        "UserGame",
        back_populates="user"
    )
    
    def __repr__(self) -> str:
      return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"


