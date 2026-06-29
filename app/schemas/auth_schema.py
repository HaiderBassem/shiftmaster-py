from pydantic import BaseModel, EmailStr
from uuid import UUID

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenPayload(BaseModel):
    sub: str | None = None
    role: str | None = None
