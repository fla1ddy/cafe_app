from fastapi import APIRouter, Depends, Request

from producer.core.dependencies import role_checker
from producer.core.rabbitmq import rabbitmq_manager
from producer.core.exceptions import InternalServerError

router = APIRouter(prefix="/group_head", tags=["group_head"])

@router.get("/slot")
async def reserve_slot(request: Request, current_user: dict = Depends(role_checker("group_head"))):
    try:
        message = {
            "action": "reserve_slot",
            "data": {
                "user_id": current_user["id"]
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