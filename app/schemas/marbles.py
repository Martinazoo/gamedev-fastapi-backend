from pydantic import BaseModel

class CreateMarbles(BaseModel):
    color: str
    user_id: str

class LeaveMarbles(BaseModel):
    id: int

