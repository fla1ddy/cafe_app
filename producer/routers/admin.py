from fastapi import APIRouter, Depends, Request

from producer.core.rabbitmq import rabbitmq_manager
from producer.core.dependencies import role_checker
from producer.core.exceptions import InternalServerError
from producer.schemas.admin import ChangeRole

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/dashboard")
async def admin_dashboard(request: Request, current_user: dict = Depends(role_checker("admin"))):
    try:
        message = {
            "action": "get_dashboard_data",
            "data": {}
        }

        response = await rabbitmq_manager.publish_message(
            routing_key="admin.dashboard",
            message=message
        )
        
        if "error" in response:
            raise InternalServerError(response["error"])
            
        return response

    except Exception as e:
        raise InternalServerError(f"Error getting dashboard data: {str(e)}")

@router.post("/assign_role")
async def assign_role(request: Request, changes: ChangeRole, current_user: dict = Depends(role_checker("admin"))):
    try:
        message = {
            "action": "assign_role",
            "data": {
                "user_email": changes.user_email,
                "new_role": changes.new_role
            }
        }

        response = await rabbitmq_manager.publish_message(
            routing_key="admin.assign_role",
            message=message
        )
        
        if "error" in response:
            raise InternalServerError(response["error"])
            
        return response

    except Exception as e:
        raise InternalServerError(f"Error assigning role: {str(e)}")

