from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from src.models.schemas import EmailRequest, EmailResponse
from src.services import gmail_service
from src.utils.response_utils import handle_service_result, create_response
import logging

# Configure logging
logger = logging.getLogger("gmail_routes")

router = APIRouter(
    prefix="/gmail",
    tags=["Gmail"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    },
)


@router.post("/setup", response_model=dict, status_code=status.HTTP_200_OK)
async def setup_gmail_integration():
    """
    Setup Gmail integration with Composio.
    Returns a URL for authentication if needed.
    """
    result = gmail_service.setup_gmail_integration()
    return handle_service_result(result, "Failed to setup Gmail integration")


@router.post("/generate", response_model=EmailResponse, status_code=status.HTTP_200_OK)
async def generate_email(request: EmailRequest):
    """
    Generate an email based on the provided prompt without sending it.
    """
    try:
        result = gmail_service.generate_email(request.content_prompt, request.is_formal)
        if not result["success"]:
            return EmailResponse(
                success=False,
                message="Failed to generate email",
                error=result.get("error", "Unknown error")
            )
        
        return EmailResponse(
            success=True,
            message="Email generated successfully",
            email_content=result["content"]
        )
    except Exception as e:
        logger.error(f"Error generating email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating email: {str(e)}"
        )


@router.post("/send", response_model=EmailResponse, status_code=status.HTTP_200_OK)
async def send_email(request: EmailRequest, background_tasks: BackgroundTasks):
    """
    Generate and send an email based on the provided prompt.
    """
    try:
        # Generate the email content
        gen_result = gmail_service.generate_email(request.content_prompt, request.is_formal)
        
        if not gen_result["success"]:
            logger.error(f"Failed to generate email: {gen_result.get('error', 'Unknown error')}")
            return EmailResponse(
                success=False,
                message="Failed to generate email",
                error=gen_result.get("error", "Unknown error")
            )
        
        email_content = gen_result["content"]
        
        # Send the email
        send_result = gmail_service.send_to_gmail(
            request.recipient_email, 
            request.subject, 
            email_content
        )
        
        if not send_result["success"]:
            logger.error(f"Failed to send email: {send_result.get('error', 'Unknown error')}")
            return EmailResponse(
                success=False,
                message="Failed to send email",
                email_content=email_content,
                error=send_result.get("error", "Unknown error")
            )
        
        logger.info(f"Email sent successfully to {request.recipient_email}")
        return EmailResponse(
            success=True,
            message=f"Email sent successfully to {request.recipient_email}",
            email_content=email_content
        )
    except Exception as e:
        logger.error(f"Error in send_email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending email: {str(e)}"
        )
