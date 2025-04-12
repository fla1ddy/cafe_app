from fastapi import APIRouter, Request

from producer.core.rabbitmq import rabbitmq_manager
from producer.core.exceptions import InternalServerError

from datetime import datetime

router = APIRouter(prefix="/guest", tags=["guest"])

@router.get("/menu")
async def get_menu(request: Request):
    try:
        message = {
            "action": "get_menu",
            "data": {}
        }

        response = await rabbitmq_manager.publish_message(
            routing_key="guest.menu",
            message=message
        )
        
        if "error" in response:
            raise InternalServerError(response["error"])
            
        return response

    except Exception as e:
        raise InternalServerError(f"Error getting menu: {str(e)}")

@router.get("/schedule")
async def get_schedule(request: Request):
    try:
        message = {
            "action": "get_schedule",
            "data": datetime.today().weekday()
        }

        response = await rabbitmq_manager.publish_message(
            routing_key="guest.schedule",
            message=message
        )
        
        if "error" in response:
            raise InternalServerError(response["error"])
        
        return response

    except Exception as e:
        raise InternalServerError(f"Error getting schedule: {str(e)}") 