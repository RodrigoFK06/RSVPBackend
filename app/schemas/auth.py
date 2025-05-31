from pydantic import BaseModel, EmailStr
from typing import Optional # Add this line

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[EmailStr] = None
    # Or user_id: Optional[str] = None, depending on what we store in JWT

class UserLogin(BaseModel):
    username: EmailStr # Using email as username
    password: str
