from fastapi import APIRouter, Depends
from src.utils.validation import test_gemini_connection, test_slack_connection, validate_api_keys
from src.config.settings import PROJECT_NAME
import platform
import sys
import time

router = APIRouter(
    prefix="/health",
    tags=["Health"],
    responses={404: {"description": "Not found"}},
)

# Track server start time
START_TIME = time.time()

def get_system_info():
    """Get system information"""
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "uptime_seconds": int(time.time() - START_TIME)
    }

@router.get("/")
async def health_check():
    """
    Basic health check endpoint
    """
    return {
        "status": "healthy",
        "service": PROJECT_NAME
    }

@router.get("/detailed")
async def detailed_health_check(system_info: dict = Depends(get_system_info)):
    """
    Detailed health check with API connection status
    """
    # Validate API keys
    keys_valid, keys_error = validate_api_keys()
    
    # Check connections only if keys are valid
    gemini_status = test_gemini_connection() if keys_valid else {"success": False, "error": keys_error}
    slack_status = test_slack_connection() if keys_valid else {"success": False, "error": keys_error}
    
    # Determine overall status
    overall_status = "healthy" if gemini_status.get("success", False) else "degraded"
    
    return {
        "status": overall_status,
        "service": PROJECT_NAME,
        "system_info": system_info,
        "api_connections": {
            "gemini": {
                "status": "connected" if gemini_status.get("success", False) else "disconnected",
                "details": gemini_status
            },
            "slack": {
                "status": "connected" if slack_status.get("success", False) else "disconnected",
                "details": slack_status
            }
        }
    }
