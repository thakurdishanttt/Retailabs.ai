from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from typing import Optional, Dict
from src.models.schemas import WhatsAppMessageRequest, WhatsAppMessageResponse, WhatsAppMediaRequest, WhatsAppTemplateRequest, WhatsAppSetupRequest
from src.services import whatsapp_service
from src.utils.response_utils import handle_service_result, create_response
import logging

# Configure logging
logger = logging.getLogger("whatsapp_routes")

router = APIRouter(
    prefix="/whatsapp",
    tags=["WhatsApp"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    },
)


@router.post("/setup", response_model=dict, status_code=status.HTTP_200_OK)
async def setup_whatsapp_integration(request: WhatsAppSetupRequest):
    """
    Setup WhatsApp integration with Composio.
    Returns a URL for authentication if needed.
    
    Requires WhatsApp Business API auth_token and phone_number_id.
    You can provide an optional entity_id in the request to create a unique WhatsApp connection.
    This allows different users to connect different WhatsApp accounts.
    """
    # Validate required parameters
    if not request.auth_token or not request.phone_number_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both auth_token and phone_number_id are required for WhatsApp integration"
        )
        
    # Use the entity_id from the request or default
    entity_id = request.entity_id if request.entity_id else "default"
    result = whatsapp_service.setup_whatsapp_integration(
        auth_token=request.auth_token,
        phone_number_id=request.phone_number_id,
        entity_id=entity_id
    )
    return handle_service_result(result, "Failed to setup WhatsApp integration")


@router.post("/generate", response_model=WhatsAppMessageResponse, status_code=status.HTTP_200_OK)
async def generate_message(request: WhatsAppMessageRequest):
    """
    Generate a WhatsApp message based on the provided prompt without sending it.
    """
    try:
        # Generate message
        result = whatsapp_service.generate_message(request.content_prompt)
        
        if not result["success"]:
            logger.error(f"Failed to generate message: {result.get('error', 'Unknown error')}")
            return WhatsAppMessageResponse(
                success=False,
                message="Failed to generate message",
                error=result.get("error", "Unknown error")
            )
        
        return WhatsAppMessageResponse(
            success=True,
            message="Message generated successfully",
            phone_number=request.phone_number,
            message_content=result["content"]
        )
    except Exception as e:
        logger.error(f"Error generating message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating message: {str(e)}"
        )


@router.post("/send", response_model=WhatsAppMessageResponse, status_code=status.HTTP_200_OK)
async def send_message(request: WhatsAppMessageRequest, background_tasks: BackgroundTasks):
    """
    Generate and send a WhatsApp message based on the provided prompt.
    
    IMPORTANT: Due to WhatsApp Business API policies, this endpoint will only deliver messages if:
    1. The recipient has messaged your WhatsApp Business number within the last 24 hours, OR
    2. You are responding to a user-initiated conversation
    
    For initial contact or messages outside the 24-hour window, use the /send-template endpoint instead.
    """
    # Add a warning log about WhatsApp's messaging restrictions
    logger.warning(
        "WhatsApp Business API RESTRICTION: Free-form messages can only be delivered if the recipient "
        "has messaged your WhatsApp Business number within the last 24 hours. "
        "For initial contact, use template messages via the /send-template endpoint."
    )
    
    try:
        # Generate the message content
        gen_result = whatsapp_service.generate_message(request.content_prompt)
        
        if not gen_result["success"]:
            logger.error(f"Failed to generate message: {gen_result.get('error', 'Unknown error')}")
            return WhatsAppMessageResponse(
                success=False,
                message="Failed to generate message",
                error=gen_result.get("error", "Unknown error")
            )
        
        message_content = gen_result["content"]
        
        # Send the message
        send_result = whatsapp_service.send_to_whatsapp(
            message=message_content, 
            phone_number=request.phone_number,
            api_key=request.api_key,
            entity_id=request.entity_id
        )
        
        if not send_result["success"]:
            logger.error(f"Failed to send message: {send_result.get('error', 'Unknown error')}")
            return WhatsAppMessageResponse(
                success=False,
                message="Failed to send message",
                phone_number=request.phone_number,
                message_content=message_content,
                error=send_result.get("error", "Unknown error")
            )
        
        logger.info(f"Message sent successfully to {request.phone_number}")
        return WhatsAppMessageResponse(
            success=True,
            message=f"Message sent successfully to {request.phone_number}",
            phone_number=request.phone_number,
            message_content=message_content
        )
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending message: {str(e)}"
        )


@router.post("/send-media", response_model=WhatsAppMessageResponse, status_code=status.HTTP_200_OK)
async def send_media(request: WhatsAppMediaRequest, background_tasks: BackgroundTasks):
    """
    Send a media message to WhatsApp with the provided media URL and caption.
    """
    try:
        # Send the media message
        send_result = whatsapp_service.send_to_whatsapp(
            message=request.caption, 
            phone_number=request.phone_number,
            message_type="media",
            media_url=request.media_url,
            api_key=request.api_key,
            entity_id=request.entity_id
        )
        
        if not send_result["success"]:
            logger.error(f"Failed to send media: {send_result.get('error', 'Unknown error')}")
            return WhatsAppMessageResponse(
                success=False,
                message="Failed to send media",
                phone_number=request.phone_number,
                error=send_result.get("error", "Unknown error")
            )
        
        logger.info(f"Media sent successfully to {request.phone_number}")
        return WhatsAppMessageResponse(
            success=True,
            message=f"Media sent successfully to {request.phone_number}",
            phone_number=request.phone_number,
            message_content=request.caption
        )
    except Exception as e:
        logger.error(f"Error in send_media: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending media: {str(e)}"
        )


@router.post("/send-template", response_model=WhatsAppMessageResponse, status_code=status.HTTP_200_OK)
async def send_template(request: WhatsAppTemplateRequest, background_tasks: BackgroundTasks):
    """
    Send a template message to WhatsApp with the provided template name and parameters.
    
    This is the RECOMMENDED way to initiate contact with users who haven't messaged you in the last 24 hours.
    Template messages can be sent to any user who has opted in to receive messages from your business.
    
    Example request:
    ```json
    {
      "template_name": "hello_world",
      "template_params": {
        "1": "John Doe"
      },
      "phone_number": "916398571463"
    }
    ```
    
    Notes:
    1. Templates must be pre-approved in your WhatsApp Business account
    2. The phone number should include country code WITHOUT the + sign
    3. Template parameters are numbered based on the variables in your template
    """
    logger.info(f"Sending WhatsApp template message '{request.template_name}' to {request.phone_number}")
    
    try:
        # Send the template message
        send_result = whatsapp_service.send_to_whatsapp(
            message="", # Not used for template messages
            phone_number=request.phone_number,
            message_type="template",
            template_name=request.template_name,
            template_params=request.template_params,
            api_key=request.api_key,
            entity_id=request.entity_id
        )
        
        if not send_result["success"]:
            logger.error(f"Failed to send template: {send_result.get('error', 'Unknown error')}")
            return WhatsAppMessageResponse(
                success=False,
                message="Failed to send template",
                phone_number=request.phone_number,
                error=send_result.get("error", "Unknown error")
            )
        
        logger.info(f"Template sent successfully to {request.phone_number}")
        return WhatsAppMessageResponse(
            success=True,
            message=f"Template sent successfully to {request.phone_number}",
            phone_number=request.phone_number
        )
    except Exception as e:
        logger.error(f"Error in send_template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending template: {str(e)}"
        )
