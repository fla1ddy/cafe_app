from fastapi import APIRouter, Request, Depends
from fastapi.security import OAuth2PasswordRequestForm
import logging

from producer.core.rabbitmq import rabbitmq_manager
from producer.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from producer.core.exceptions import UnauthorizedError, InternalServerError
from producer.schemas.user import RegisterModel, TokenResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=dict)
async def register(request: Request, user: RegisterModel):
    try:
        hashed_pwd = hash_password(user.password)

        message = {
            "action": "register_user",
            "data": {
                "username": user.username,
                "password": hashed_pwd,
                "role": user.role,
                "group": user.group
            }
        }

        response = await rabbitmq_manager.publish_message(
            routing_key="user.register",
            message=message
        )
        
        if "error" in response:
            raise InternalServerError(response["error"])
            
        return response

    except Exception as e:
        raise InternalServerError(f"Registration error: {str(e)}")

@router.post("/login", response_model=TokenResponse)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        logger.info(f"Login attempt for user: {form_data.username}")
        
        message = {
            "action": "get_user_by_username",
            "data": {
                "username": form_data.username,
                "password": form_data.password
            }
        }

        response = await rabbitmq_manager.publish_message(
            routing_key="user.login",
            message=message
        )

        if "error" in response:
            logger.error(f"Login error from consumer: {response['error']}")
            raise InternalServerError(response["error"])

        logger.info(f"User found in database: {response}")
        logger.info(f"Attempting to verify password for user: {form_data.username}")

        if not verify_password(form_data.password, response["password"]):
            raise UnauthorizedError("Incorrect password")

        token_data = {
            "sub": str(response["id"]),
            "role": str(response["role"])
        }

        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)

        logger.info(f"Successful login for user: {form_data.username}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise InternalServerError(f"Login error: {str(e)}")
