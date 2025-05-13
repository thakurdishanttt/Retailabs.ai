from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from typing import Optional, Dict
from src.models.linkedin_schemas import (
    LinkedInSetupRequest,
    LinkedInConnectionRequest,
    LinkedInMessageRequest,
    LinkedInPostRequest,
    LinkedInProfileSearchRequest,
    LinkedInResponse,
    LinkedInProfilesResponse
)
from pydantic import BaseModel
from typing import List, Dict
from src.services import linkedin_service
from src.utils.response_utils import handle_service_result, create_response
import logging

# Configure logging
logger = logging.getLogger("linkedin_routes")

router = APIRouter(
    prefix="/linkedin",
    tags=["LinkedIn"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    },
)


@router.post("/setup", response_model=LinkedInResponse, status_code=status.HTTP_200_OK)
async def setup_linkedin_integration(request: LinkedInSetupRequest = None):
    """
    Setup LinkedIn integration with Composio.
    Returns a URL for authentication if needed.
    """
    # Use default entity_id if request is None
    entity_id = request.entity_id if request and request.entity_id else "default"
    
    # Always use the Composio API key from settings for setup
    result = linkedin_service.setup_linkedin_integration()
    
    if result.get("success"):
        return LinkedInResponse(
            success=True,
            message=result.get("message", "LinkedIn integration setup successful"),
            data={"redirect_url": result.get("redirect_url")} if "redirect_url" in result else None
        )
    else:
        return LinkedInResponse(
            success=False,
            message="Failed to setup LinkedIn integration",
            error=result.get("message", "Unknown error")
        )


@router.post("/search-profiles", response_model=LinkedInProfilesResponse, status_code=status.HTTP_200_OK)
async def search_profiles(request: LinkedInProfileSearchRequest):
    """
    Search for LinkedIn profiles based on keywords.
    
    Parameters:
    - keywords: Search keywords
    - access_token: LinkedIn access token
    - limit: Maximum number of results to return (default: 10)
    """
    try:
        # Validate access token
        if not request.access_token or request.access_token == "string":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid LinkedIn access token must be provided"
            )
            
        # Search profiles using the service
        result = linkedin_service.search_profiles(
            keywords=request.keywords,
            access_token=request.access_token,
            limit=request.limit,
            entity_id=request.entity_id
        )
        
        if not result.get("success"):
            return LinkedInProfilesResponse(
                success=False,
                message="Failed to search profiles",
                profiles=[],
                error=result.get("error", "Unknown error")
            )
            
        return LinkedInProfilesResponse(
            success=True,
            message=result.get("message", "Profiles found"),
            profiles=result.get("profiles", [])
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching profiles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching profiles: {str(e)}"
        )


@router.post("/connect", response_model=LinkedInResponse, status_code=status.HTTP_200_OK)
async def send_connection_request(request: LinkedInConnectionRequest):
    """
    Send a LinkedIn connection request.
    
    Parameters:
    - profile_url: URL of the LinkedIn profile to connect with
    - message: Optional personalized message for the connection request
    - access_token: LinkedIn access token
    """
    try:
        # Validate access token
        if not request.access_token or request.access_token == "string":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid LinkedIn access token must be provided"
            )
            
        # Generate a message if not provided
        message = request.message
        if not message:
            gen_result = linkedin_service.generate_message(
                f"Write a brief, professional LinkedIn connection request message that is concise and friendly."
            )
            if gen_result.get("success"):
                message = gen_result.get("content")
            else:
                message = "I'd like to connect with you on LinkedIn."
        
        # Send connection request
        result = linkedin_service.send_connection_request(
            profile_url=request.profile_url,
            message=message,
            access_token=request.access_token,
            entity_id=request.entity_id
        )
        
        if not result.get("success"):
            return LinkedInResponse(
                success=False,
                message="Failed to send connection request",
                error=result.get("error", "Unknown error")
            )
            
        return LinkedInResponse(
            success=True,
            message=result.get("message", "Connection request sent successfully"),
            data={"message_sent": message}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending connection request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending connection request: {str(e)}"
        )


@router.post("/message", response_model=LinkedInResponse, status_code=status.HTTP_200_OK)
async def send_message(request: LinkedInMessageRequest, background_tasks: BackgroundTasks):
    """
    Generate and send a LinkedIn message based on the provided prompt.
    
    Parameters:
    - profile_id: LinkedIn profile ID to message
    - content_prompt: Prompt describing the message to generate
    - access_token: LinkedIn access token
    """
    try:
        # Validate access token
        if not request.access_token or request.access_token == "string":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid LinkedIn access token must be provided"
            )
            
        # Generate the message content
        gen_result = linkedin_service.generate_message(request.content_prompt)
        
        if not gen_result.get("success"):
            logger.error(f"Failed to generate message: {gen_result.get('error', 'Unknown error')}")
            return LinkedInResponse(
                success=False,
                message="Failed to generate message",
                error=gen_result.get("error", "Unknown error")
            )
        
        message_content = gen_result.get("content")
        
        # Send the message
        send_result = linkedin_service.send_message(
            profile_id=request.profile_id,
            message=message_content,
            access_token=request.access_token,
            entity_id=request.entity_id
        )
        
        if not send_result.get("success"):
            logger.error(f"Failed to send message: {send_result.get('error', 'Unknown error')}")
            return LinkedInResponse(
                success=False,
                message="Failed to send message",
                data={"message_content": message_content},
                error=send_result.get("error", "Unknown error")
            )
        
        logger.info(f"Message sent successfully to profile {request.profile_id}")
        return LinkedInResponse(
            success=True,
            message="Message sent successfully",
            data={"message_content": message_content}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending message: {str(e)}"
        )


@router.post("/post", response_model=LinkedInResponse, status_code=status.HTTP_200_OK)
async def create_post(request: LinkedInPostRequest):
    """
    Generate and create a LinkedIn post based on the provided prompt.
    
    Parameters:
    - content_prompt: Prompt describing the post to generate
    - access_token: LinkedIn access token
    - image_url: Optional URL of an image to include in the post
    - article_url: Optional URL of an article to share in the post
    """
    try:
        # Validate access token
        if not request.access_token or request.access_token == "string":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid LinkedIn access token must be provided"
            )
            
        # Generate the post content
        gen_result = linkedin_service.generate_message(request.content_prompt)
        
        if not gen_result.get("success"):
            logger.error(f"Failed to generate post content: {gen_result.get('error', 'Unknown error')}")
            return LinkedInResponse(
                success=False,
                message="Failed to generate post content",
                error=gen_result.get("error", "Unknown error")
            )
        
        post_content = gen_result.get("content")
        
        # Create the post
        post_result = linkedin_service.create_post(
            content=post_content,
            access_token=request.access_token,
            image_url=request.image_url,
            article_url=request.article_url,
            entity_id=request.entity_id
        )
        
        if not post_result.get("success"):
            logger.error(f"Failed to create post: {post_result.get('error', 'Unknown error')}")
            return LinkedInResponse(
                success=False,
                message="Failed to create post",
                data={"post_content": post_content},
                error=post_result.get("error", "Unknown error")
            )
        
        logger.info("LinkedIn post created successfully")
        return LinkedInResponse(
            success=True,
            message="Post created successfully",
            data={
                "post_content": post_content,
                "post_id": post_result.get("data", {}).get("post_id")
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating post: {str(e)}"
        )


class ActionInfo(BaseModel):
    name: str
    description: str


class ActionsResponse(BaseModel):
    success: bool
    message: str
    actions: List[ActionInfo] = []
    error: Optional[str] = None


@router.get("/actions", response_model=ActionsResponse, status_code=status.HTTP_200_OK)
async def list_actions():
    """
    List all available LinkedIn actions from Composio.
    This helps identify the correct action names to use in the API.
    """
    try:
        result = linkedin_service.list_available_actions()
        
        if not result.get("success"):
            return ActionsResponse(
                success=False,
                message="Failed to list LinkedIn actions",
                actions=[],
                error=result.get("error", "Unknown error")
            )
            
        actions = [ActionInfo(name=action["name"], description=action["description"]) 
                  for action in result.get("actions", [])]
        
        return ActionsResponse(
            success=True,
            message=result.get("message", "LinkedIn actions retrieved"),
            actions=actions
        )
    except Exception as e:
        logger.error(f"Error listing LinkedIn actions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing LinkedIn actions: {str(e)}"
        )
