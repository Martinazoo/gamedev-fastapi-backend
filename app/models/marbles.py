from typing import List
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base

class Marble(Base):
    __tablename__ = "marbles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    color: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
