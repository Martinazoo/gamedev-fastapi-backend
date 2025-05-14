from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base

class MarblesDemo(Base):
    __tablename__ = "marblesdemo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    color: Mapped[str] = mapped_column(String(20), nullable=False)
    username: Mapped[str] = mapped_column(String(35), nullable=False)
    
