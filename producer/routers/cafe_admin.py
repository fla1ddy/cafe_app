from fastapi import APIRouter, Depends, Request

from producer.core.rabbitmq import rabbitmq_manager
from producer.core.dependencies import role_checker
from producer.core.exceptions import InternalServerError

from producer.schemas.cafe_admin import ScheduleModel, MenuModel

router = APIRouter(prefix="/cafe_admin", tags=["cafe_admin"])

@router.post("/menu")
async def update_menu(request: Request, menu: MenuModel, current_user: dict = Depends(role_checker("cafe_admin"))):
    try:
        message = {
            "action": "update_menu",
            "data": menu.dict()
        }

        response = await rabbitmq_manager.publish_message(
            routing_key="cafe_admin.menu",
            message=message
        )
        
        if "error" in response:
            raise InternalServerError(response["error"])
            
        return response

    except Exception as e:
        raise InternalServerError(f"Error updating menu: {str(e)}")

@router.post("/schedule")
async def update_schedule(request: Request, schedule: ScheduleModel, current_user: dict = Depends(role_checker("cafe_admin"))):
    try:
        message = {
            "action": "update_schedule",
            "data": schedule.dict()
        }

        response = await rabbitmq_manager.publish_message(
            routing_key="cafe_admin.schedule",
            message=message
        )
        
        if "error" in response:
            raise InternalServerError(response["error"])
            
        return response

    except Exception as e:
        raise InternalServerError(f"Error updating schedule: {str(e)}")
