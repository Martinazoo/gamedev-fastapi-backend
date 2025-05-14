from pydantic import BaseModel, EmailStr, field_validator
import re
class UserRegister(BaseModel):
    username: str
    fullname: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v
class UserLogin(BaseModel):
    email: str
    password: str
