from pydantic import BaseModel, EmailStr, Field

class ChangeRole(BaseModel):
    user_email: EmailStr
    new_role: str = Field(..., example="student")