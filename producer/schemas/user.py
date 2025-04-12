from pydantic import BaseModel, Field
from typing import Optional

class RegisterModel(BaseModel):  # Changed to inherit from BaseModel since we don't need id and role from User
    username: str = Field(..., example="ivanov")
    password: str = Field(..., min_length=4, example="1234")
    role: str = "student"
    group: Optional[str] = None

class LoginModel(BaseModel):  # Changed to inherit from BaseModel since we only need email and password
    username: str = Field(..., example="ivanov")
    password: str = Field(..., min_length=4, example="1234")  # Added validation and example

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
