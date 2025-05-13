from sqlalchemy import Column, Integer, Table, String, ForeignKey
from app.db.base import Base
from sqlalchemy.orm import relationship, Mapped, mapped_column, relationship
from typing import Optional, List


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    fullname: Mapped[str] = mapped_column(String(40), nullable=False)
    email: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    profile_image: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    total_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
