from fastapi import APIRouter, Depends
from utilities.users import get_current_user
from models import db
from models.user import User
from utilities.users import require_login
from utilities.api_client import verify_api_key

router = APIRouter(prefix="/api/v1/users", tags=["Users"])

@router.get("/me/settings")
async def get_user_settings(current_user: User = Depends(get_current_user), _: str = Depends(verify_api_key)):
    """
    Get current user's sharing/privacy settings.
    """
    return {
        "allow_sharing_from_nonfriends": False,  # Replace with real setting
        "notifications_enabled": True
    }

@router.post("/me/settings")
async def update_user_settings(settings: dict, current_user: User = Depends(get_current_user), _: str = Depends(verify_api_key)):
    """
    Update sharing/privacy settings.
    """
    # TODO: Validate and update
    return {"message": "Settings updated."}

@router.post("/block/{username}")
async def block_user(username: str, current_user: User = Depends(get_current_user), _: str = Depends(verify_api_key)):
    """
    Block a user from sharing or sending friend requests.
    """
    return {"message": f"{username} has been blocked."}

@router.get("/block/list")
async def get_blocked_users(current_user: User = Depends(get_current_user), _: str = Depends(verify_api_key)):
    """
    List users you've blocked.
    """
    return {"blocked": []}
