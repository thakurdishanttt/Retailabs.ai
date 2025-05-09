from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from typing import Optional, Dict
from src.models.schemas import SlackMessageRequest, SlackMessageResponse, ChannelListResponse, SlackChannelInfo
from src.services import slack_service
from src.utils.response_utils import handle_service_result, create_response
import logging

# Configure logging
logger = logging.getLogger("slack_routes")

router = APIRouter(
    prefix="/slack",
    tags=["Slack"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    },
)


@router.post("/setup", response_model=dict, status_code=status.HTTP_200_OK)
async def setup_slack_integration():
    """
    Setup Slack integration with Composio.
    Returns a URL for authentication if needed.
    """
    # Always use the Composio API key from settings for setup
    result = slack_service.setup_slack_integration()
    return handle_service_result(result, "Failed to setup Slack integration")


@router.get("/channels", response_model=ChannelListResponse, status_code=status.HTTP_200_OK)
async def get_channels(bot_token: str):
    """
    Fetch available Slack channels using the provided bot token.
    
    Parameters:
    - bot_token: Slack bot token to use for authentication
    """
    try:
        # Validate bot token
        if not bot_token or bot_token == "string":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid Slack bot token must be provided"
            )
            
        # Fetch channels using the provided bot token
        channels_data = slack_service.get_channels(bot_token)
        channels = [SlackChannelInfo(id=channel["id"], name=channel["name"]) for channel in channels_data]
        return ChannelListResponse(channels=channels)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting channels: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving channels: {str(e)}"
        )


@router.post("/generate", response_model=SlackMessageResponse, status_code=status.HTTP_200_OK)
async def generate_message(request: SlackMessageRequest):
    """
    Generate a Slack message based on the provided prompt without sending it.
    """
    try:
        # Use channel name from request or a default placeholder
        channel_name = request.channel_name or "channel"
        
        # Generate message
        result = slack_service.generate_message(request.content_prompt)
        
        if not result["success"]:
            logger.error(f"Failed to generate message: {result.get('error', 'Unknown error')}")
            return SlackMessageResponse(
                success=False,
                message="Failed to generate message",
                error=result.get("error", "Unknown error")
            )
        
        return SlackMessageResponse(
            success=True,
            message="Message generated successfully",
            channel_name=channel_name,
            message_content=result["content"]
        )
    except Exception as e:
        logger.error(f"Error generating message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating message: {str(e)}"
        )


@router.post("/send", response_model=SlackMessageResponse, status_code=status.HTTP_200_OK)
async def send_message(request: SlackMessageRequest, background_tasks: BackgroundTasks):
    """
    Generate and send a Slack message based on the provided prompt.
    """
    try:
        # Get channel name - prefer the one provided in the request
        channel_name = request.channel_name or slack_service.get_channel_name(request.channel_id)
        
        # Generate the message content
        gen_result = slack_service.generate_message(request.content_prompt)
        
        if not gen_result["success"]:
            logger.error(f"Failed to generate message: {gen_result.get('error', 'Unknown error')}")
            return SlackMessageResponse(
                success=False,
                message="Failed to generate message",
                error=gen_result.get("error", "Unknown error")
            )
        
        message_content = gen_result["content"]
        
        # Send the message
        send_result = slack_service.send_to_slack(
            message=message_content, 
            channel_id=request.channel_id,
            channel_name=request.channel_name,
            bot_token=request.bot_token
        )
        
        if not send_result["success"]:
            logger.error(f"Failed to send message: {send_result.get('error', 'Unknown error')}")
            return SlackMessageResponse(
                success=False,
                message="Failed to send message",
                channel_name=channel_name,
                message_content=message_content,
                error=send_result.get("error", "Unknown error")
            )
        
        # Always use the channel name from the request
        display_channel = request.channel_name or "channel"
        logger.info(f"Message sent successfully to #{display_channel}")
        return SlackMessageResponse(
            success=True,
            message=f"Message sent successfully to #{display_channel}",
            channel_name=display_channel,
            message_content=message_content
        )
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending message: {str(e)}"
        )
