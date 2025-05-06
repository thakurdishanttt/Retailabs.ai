from fastapi import HTTPException
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def handle_service_result(result: Dict[str, Any], error_message: str, status_code: int = 500) -> Dict[str, Any]:
    """
    Handle service result and raise HTTPException if there's an error
    
    Args:
        result: Result dictionary from service function
        error_message: Error message to include in the exception
        status_code: HTTP status code for the exception
        
    Returns:
        The result dictionary if successful
        
    Raises:
        HTTPException: If the result indicates failure
    """
    if not result.get("success", False):
        error = result.get("error", "Unknown error")
        logger.error(f"{error_message}: {error}")
        raise HTTPException(
            status_code=status_code,
            detail=f"{error_message}: {error}"
        )
    return result


def create_response(
    success: bool, 
    message: str, 
    data: Optional[Dict[str, Any]] = None, 
    error: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized API response
    
    Args:
        success: Whether the operation was successful
        message: A message describing the result
        data: Optional data to include in the response
        error: Optional error message
        
    Returns:
        A dictionary with standardized response format
    """
    response = {
        "success": success,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
        
    if error is not None:
        response["error"] = error
        
    return response
