from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from producer.core.config import settings
from producer.core.security import verify_token
from producer.core.exceptions import UnauthorizedError, ForbiddenError

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=settings.OAUTH2_TOKEN_URL,
    scheme_name=settings.OAUTH2_SCHEME_NAME
)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = verify_token(token)
    
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")
        
    user_id = payload.get("sub")
    user_role = payload.get("role")

    if user_id is None or user_role is None:
        raise UnauthorizedError("Invalid token payload")
        
    return {"id": user_id, "role": user_role}

def role_checker(required_role: str):
    def _role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role:
            raise ForbiddenError(f"Access allowed only for users with role {required_role}")
        return current_user
    return _role_checker
