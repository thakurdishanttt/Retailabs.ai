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


def setup_gmail_integration(entity_id="default"):
    """Setup Gmail integration if not already done
    
    Args:
        entity_id (str, optional): A unique identifier for this Gmail connection.
                                  This allows different users to connect different Gmail accounts.
                                  Defaults to "default".
    """
    try:
        
        # Get the Composio Entity object for this user
        entity = composio_tool_set.get_entity(id=entity_id)
        
        # Initiate connection to Gmail with the provided entity
        response = composio_tool_set.initiate_connection(
            app="GMAIL",
            entity_id=entity_id
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
                    id=response.connectedAccountId,
                    entity_id=entity_id  # Ensure we're checking the connection for the right entity
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


def generate_subject(prompt):
    """Generate an appropriate subject line for an email based on the prompt
    
    Args:
        prompt (str): The prompt describing the email content
        
    Returns:
        dict: Dictionary with success status and generated subject
    """
    try:
        # Use the default initialized client
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        subject_prompt = f"""
        Create a concise and relevant subject line for an email based on this instruction:
        "{prompt}"
        
        The subject should be:
        - Brief (5-8 words maximum)
        - Descriptive of the email's main purpose
        - Professional
        - Without any quotes or special formatting
        
        Return only the subject text, nothing else.
        """
        
        # Generate the response
        response = model.generate_content(subject_prompt)
        
        # Clean up the subject (remove quotes, extra spaces, etc.)
        subject = response.text.strip().strip('"').strip('\'').strip()
        
        return {
            "success": True,
            "subject": subject
        }
    
    except Exception as e:
        logger.error(f"Error generating subject: {str(e)}")
        return {
            "success": False,
            "error": f"Error generating subject: {str(e)}"
        }


def generate_email(prompt, is_formal=True, recipient_name=None, sender_name=None, sender_designation=None):
    """Generate a professional email message using Google Gemini
    
    Args:
        prompt (str): The prompt describing what email to generate
        is_formal (bool, optional): Whether to use formal tone. Defaults to True.
        recipient_name (str, optional): Name of the recipient to personalize the email
        sender_name (str, optional): Name of the sender to include in the signature
        sender_designation (str, optional): Job title or designation of the sender
    """
    try:
        # Use the default initialized client
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Create a detailed prompt
        tone = "formal and professional" if is_formal else "friendly and conversational"
        
        # Add recipient and sender information if provided
        recipient_info = f"\nThe email is addressed to {recipient_name}." if recipient_name else ""
        sender_info = ""
        if sender_name:
            sender_info = f"\nThe email is from {sender_name}"
            if sender_designation:
                sender_info += f", {sender_designation}"
        
        detailed_prompt = f"""
        Create a {tone} email message based on this instruction:
        "{prompt}"
        {recipient_info}{sender_info}
        
        The email should be:
        - Clear and concise
        - {tone} in tone
        - Include appropriate greeting (using recipient's name if provided) and sign-off (using sender's name and designation if provided)
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


def send_to_gmail(recipient_email, subject, message_body, entity_id="default"):
    """Send the email using Composio's Gmail integration
    
    Args:
        recipient_email (str): Email address of the recipient
        subject (str): Subject of the email
        message_body (str): Body content of the email
        entity_id (str, optional): The entity ID used to identify which Gmail account to use.
                                  This should match the entity_id used during setup.
                                  Defaults to "default".
    """
    try:
        # According to Composio docs, entity_id should be passed as a separate parameter, not in the params dict
        response = composio_tool_set.execute_action(
            action=Action.GMAIL_SEND_EMAIL,
            params={
                "recipient_email": recipient_email,
                "subject": subject,
                "body": message_body
            },
            entity_id=entity_id  # This is the correct way to specify which user's Gmail account to use
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
