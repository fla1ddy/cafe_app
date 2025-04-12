from fastapi import APIRouter, Depends, Request

from producer.core.dependencies import get_current_user, role_checker
from producer.core.rabbitmq import rabbitmq_manager
from producer.core.exceptions import InternalServerError

router = APIRouter(prefix="/group_head", tags=["group_head"])

@router.post("/reserve_slot")
async def reserve_slot(request: Request, weekday: int, schedule_item_type: str, slot_start_time: str, current_user: dict = Depends(role_checker("group_head"))):
    try:
        message = {
            "action": "reserve_slot",
            "data": {
                "user_id": current_user["id"],
                "weekday": weekday,
                "schedule_item_type": schedule_item_type,
                "slot_start_time": slot_start_time
            }
        }

        response = await rabbitmq_manager.publish_message(
            routing_key="group_head.slot",
            message=message
        )
        
        if "error" in response:
            raise InternalServerError(response["error"])
            
        return response

    except Exception as e:
        raise InternalServerError(f"Error reserving slot: {str(e)}")

@router.get("/group_choices")
async def get_group_choices(request: Request, current_user: dict = Depends(role_checker("group_head"))):
    try:
        message = {
            "action": "get_group_choices",
            "data": {
                "user_id": current_user["id"]
            }
        }

        response = await rabbitmq_manager.publish_message(
            routing_key="group_head.choices",
            message=message
        )
        
        if "error" in response:
            raise InternalServerError(response["error"])
            
        return response

    except Exception as e:
        raise InternalServerError(f"Error getting group choices: {str(e)}")