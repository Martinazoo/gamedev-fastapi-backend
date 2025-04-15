from app.db.session import SessionLocal
from app.db.base import Base
from app.db.session import engine
from app.models import Game, User, UserGame

Base.metadata.create_all(bind=engine)