from pydantic import BaseModel

class Ranking(BaseModel):
    username: str
    score: int
    gamename: str