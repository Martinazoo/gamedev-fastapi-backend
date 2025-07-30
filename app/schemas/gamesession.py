# app/schemas/game.py

from pydantic import BaseModel
from datetime import datetime

class SubmitGameSession(BaseModel):
    username: str
    gamename: str
    score: int