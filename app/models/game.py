from sqlalchemy import Column, Integer, Table, String, ForeignKey
from app.db.base import Base
from sqlalchemy.orm import relationship, Mapped, mapped_column, relationship
from typing import Optional, List
class Game(Base):
    __tablename__= "games"
    
    id: Mapped[int] = mapped_column(primary_key=True, nullable=False, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    max_score: Mapped[int] = mapped_column(nullable=False, default=0)
    played_by: Mapped[List["UserGame"]] = relationship( # type: ignore
        "UserGame",
        back_populates="game"
    )
    
