from fastapi import APIRouter, HTTPException, status, Depends
from src.services import gmail_service
import logging
from src.models.schemas import GmailSetupRequest
from pydantic import BaseModel
from typing import Optional

# Configure logging
logger = logging.getLogger("auth_routes")

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    },
)

class UserAuthRequest(BaseModel):
    username: str
    password: Optional[str] = None
    email: Optional[str] = None

@router.post("/gmail/connect", response_model=dict, status_code=status.HTTP_200_OK)
async def connect_gmail(request: GmailSetupRequest):
    """
    Connect to Gmail using the platform's Composio integration.
    
    This endpoint allows users to connect their Gmail account to the platform.
    The platform handles all API key management internally.
    
    Provide an entity_id in the request to create a unique Gmail connection.
    This ensures emails are sent from the correct Gmail account.
    
    Returns a URL for authentication if needed.
    """
    try:
        # Use the provided entity_id to create a unique connection
        result = gmail_service.setup_gmail_integration(entity_id=request.entity_id)
        
        if not result.get("success", False):
            logger.error(f"Failed to setup Gmail integration: {result.get('message', 'Unknown error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Failed to setup Gmail integration")
            )
        
        return {
            "success": True,
            "message": result.get("message", "Gmail connection initiated successfully"),
            "redirect_url": result.get("redirect_url")
        }
    except Exception as e:
        logger.error(f"Error setting up Gmail integration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting up Gmail integration: {str(e)}"
        )
