from pydantic import BaseModel

class UserRegister(BaseModel):
    username: str
    fullname: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str
