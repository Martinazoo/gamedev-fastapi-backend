from pydantic import BaseModel

class CreateMarbles(BaseModel):
    color: str
    username: str

class LeaveMarbles(BaseModel):
    username: str

