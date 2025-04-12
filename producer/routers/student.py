from fastapi import APIRouter, Depends, Request

from producer.core.rabbitmq import rabbitmq_manager
from producer.core.dependencies import get_current_user
from producer.core.exceptions import ForbiddenError, InternalServerError

router = APIRouter(prefix="/student", tags=["student"])

@router.get("/profile")
async def get_profile(request: Request, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["student", "group_head"]:
        raise ForbiddenError("Access allowed only for students")
    
    try:
        message = {
            "action": "get_student_profile",
            "data": {
                "user_id": current_user["id"]
            }
        }

        response = await rabbitmq_manager.publish_message(
            routing_key="student.profile",
            message=message
        )

        if "error" in response:
            raise InternalServerError(response["error"])
            
        return response

    except Exception as e:
        raise InternalServerError(f"Error getting profile: {str(e)}")

@router.post("/confirm_meal")
async def confirm_meal(request: Request, having_meal: bool, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "student":
        raise ForbiddenError("Access allowed only for students")
    
    try:
        message = {
            "action": "update_meal_status",
            "data": {
                "user_id": current_user["id"],
                "having_meal": having_meal
            }
        }
        
        response = await rabbitmq_manager.publish_message(
            routing_key="student.meal_status",
            message=message
        )
        
        if "error" in response:
            raise InternalServerError(response["error"])
            
        return response
        
    except Exception as e:
        raise InternalServerError(f"Error updating meal status: {str(e)}")