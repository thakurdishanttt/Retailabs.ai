import os
import logging
import google.generativeai as genai
from composio_openai import ComposioToolSet, Action
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from src.config.settings import GEMINI_API_KEY, COMPOSIO_API_KEY

# Configure logging
logger = logging.getLogger("gmail_service")

# Initialize Google Gemini API client
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Composio tool set with API key
composio_tool_set = ComposioToolSet(api_key=COMPOSIO_API_KEY)


def setup_gmail_integration():
    """Setup Gmail integration if not already done"""
    try:
        # Initiate connection to Gmail
        response = composio_tool_set.initiate_connection(
            app="GMAIL",
            entity_id="default"
        )
        
        # Access properties directly instead of using .get()
        if response and hasattr(response, 'redirectUrl'):
            logger.info("Gmail authentication URL generated")
            return {
                "success": True,
                "redirect_url": response.redirectUrl,
                "message": "Please complete Gmail authentication by opening this URL in your browser"
            }
            
            # Check if connection is active
            if hasattr(response, 'connectedAccountId'):
                connection = composio_tool_set.get_connected_account(
                    id=response.connectedAccountId
                )
                # Check status directly as property
                if connection and hasattr(connection, 'status') and connection.status == "ACTIVE":
                    logger.info("Gmail connection is active")
                    return {
                        "success": True,
                        "message": "Gmail connection is active"
                    }
        
        return {
            "success": False,
            "message": "Failed to setup Gmail integration"
        }
        
    except Exception as e:
        logger.error(f"Error setting up Gmail integration: {str(e)}")
        return {
            "success": False,
            "message": f"Error setting up Gmail integration: {str(e)}"
        }


def generate_email(prompt, is_formal=True):
    """Generate a professional email message using Google Gemini"""
    try:
        # Initialize the model - use the latest available model
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Create a detailed prompt
        tone = "formal and professional" if is_formal else "friendly and conversational"
        detailed_prompt = f"""
        Create a {tone} email message based on this instruction:
        "{prompt}"
        
        The email should be:
        - Clear and concise
        - {tone} in tone
        - Include appropriate greeting and sign-off
        - Include any important details mentioned in the instruction
        - Well-structured with paragraphs as needed
        
        Return only the email body text, nothing else.
        """
        
        # Generate the response
        response = model.generate_content(detailed_prompt)
        return {
            "success": True,
            "content": response.text
        }
    
    except Exception as e:
        logger.error(f"Error generating email: {str(e)}")
        return {
            "success": False,
            "error": f"Error generating email: {str(e)}"
        }


def send_to_gmail(recipient_email, subject, message_body):
    """Send the email using Composio's Gmail integration"""
    try:
        # Use the correct parameter names for the Gmail action
        response = composio_tool_set.execute_action(
            Action.GMAIL_SEND_EMAIL,
            {
                "recipient_email": recipient_email,
                "subject": subject,
                "body": message_body
            }
        )
        
        logger.info(f"Gmail API response: {response}")
        
        # Check if response is successful by examining its structure and content
        if response:
            # Check for success information in different structures
            if hasattr(response, 'successfull') and response.successfull:
                return {"success": True, "message": f"Email successfully sent to {recipient_email}"}
            elif hasattr(response, 'success') and response.success:
                return {"success": True, "message": f"Email successfully sent to {recipient_email}"}
            elif hasattr(response, 'data') and response.data:
                return {"success": True, "message": f"Email successfully sent to {recipient_email}"}
            elif isinstance(response, dict) and response.get('successfull'):
                return {"success": True, "message": f"Email successfully sent to {recipient_email}"}
            elif isinstance(response, dict) and response.get('success'):
                return {"success": True, "message": f"Email successfully sent to {recipient_email}"}
            elif isinstance(response, dict) and 'data' in response and response['data']:
                return {"success": True, "message": f"Email successfully sent to {recipient_email}"}
        
        # If none of the success checks passed, return error
        error_message = None
        if hasattr(response, 'error'):
            error_message = response.error
        elif isinstance(response, dict) and 'error' in response:
            error_message = response['error']
            
        return {
            "success": False,
            "error": f"Failed to send email: {error_message or 'Unknown error in response format'}"
        }
    
    except Exception as e:
        logger.error(f"Error using Composio API for Gmail: {str(e)}")
        return {
            "success": False,
            "error": f"Error using Composio API for Gmail: {str(e)}"
        }
