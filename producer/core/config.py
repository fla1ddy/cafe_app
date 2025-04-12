from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Security settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"  # Default to HS256
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OAuth2 settings
    OAUTH2_TOKEN_URL: str = "/auth/login"
    OAUTH2_SCHEME_NAME: str = "OAuth2PasswordBearer"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
