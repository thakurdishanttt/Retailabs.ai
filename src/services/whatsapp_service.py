import os
import logging
import google.generativeai as genai
from composio_openai import ComposioToolSet, Action
from src.config.settings import GEMINI_API_KEY, COMPOSIO_API_KEY
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger("whatsapp_service")

# Initialize Google Gemini API client
genai.configure(api_key=GEMINI_API_KEY)

# Token cache to store valid API keys
# Format: {phone_number: {"api_key": "api_key", "expires": datetime}}
api_key_cache = {}


def setup_whatsapp_integration(auth_token, phone_number_id, entity_id="default"):
    """Setup WhatsApp integration if not already done
    
    Args:
        auth_token (str): WhatsApp Business API authentication token
        phone_number_id (str): WhatsApp Business API phone number ID
        entity_id (str, optional): A unique identifier for this WhatsApp connection.
                                  This allows different users to connect different WhatsApp accounts.
                                  Defaults to "default".
    """
    try:
        # Always use the Composio API key from settings for setup
        composio_tool_set = ComposioToolSet(api_key=COMPOSIO_API_KEY)
        
        # Get the Composio Entity object for this user
        entity = composio_tool_set.get_entity(id=entity_id)
        
        # Initiate connection to WhatsApp with required parameters
        response = composio_tool_set.initiate_connection(
            app="WHATSAPP",
            entity_id=entity_id,
            connected_account_params={
                "auth_token": auth_token,
                "phone_number_id": phone_number_id
            }
        )
        
        # Access properties directly instead of using .get()
        if response:
            # Check if we have a redirect URL for authentication
            if hasattr(response, 'redirectUrl') and response.redirectUrl:
                logger.info("WhatsApp authentication URL generated")
                return {
                    "success": True,
                    "redirect_url": response.redirectUrl,
                    "message": "Please complete WhatsApp authentication by opening this URL in your browser"
                }
            
            # Check if connection is already active
            if hasattr(response, 'connectedAccountId'):
                connection = composio_tool_set.get_connected_account(
                    id=response.connectedAccountId,
                    entity_id=entity_id  # Ensure we're checking the connection for the right entity
                )
                # Check status directly as property
                if connection and hasattr(connection, 'status') and connection.status == "ACTIVE":
                    logger.info("WhatsApp connection is active")
                    return {
                        "success": True,
                        "message": "WhatsApp connection is active"
                    }
            
            # If we get here, the connection was created but doesn't need a redirect URL
            # This happens when using API key authentication instead of OAuth
            logger.info("WhatsApp connection created successfully with API credentials")
            return {
                "success": True,
                "message": "WhatsApp connection created successfully with your API credentials"
            }
        
        return {
            "success": False,
            "message": "Failed to setup WhatsApp integration"
        }
        
    except Exception as e:
        logger.error(f"Error setting up WhatsApp integration: {str(e)}")
        return {
            "success": False,
            "message": f"Error setting up WhatsApp integration: {str(e)}"
        }


def store_api_key_for_phone(phone_number, api_key):
    """Store an API key for a specific phone number
    
    Args:
        phone_number (str): The recipient's WhatsApp phone number
        api_key (str): The WhatsApp API key to store
    """
    if phone_number and api_key and api_key != "string":
        # Store the API key with a 24-hour expiration
        api_key_cache[phone_number] = {
            "api_key": api_key,
            "expires": datetime.now() + timedelta(hours=24)
        }
        logger.info(f"Stored API key for phone number {phone_number}")


def get_api_key_for_phone(phone_number):
    """Get a stored API key for a specific phone number
    
    Args:
        phone_number (str): The recipient's WhatsApp phone number
        
    Returns:
        str or None: The stored API key, or None if not found or expired
    """
    if phone_number in api_key_cache:
        cache_entry = api_key_cache[phone_number]
        # Check if the API key is still valid
        if cache_entry["expires"] > datetime.now():
            logger.info(f"Using cached API key for phone number {phone_number}")
            return cache_entry["api_key"]
        else:
            # API key expired, remove it from cache
            logger.info(f"API key for phone number {phone_number} expired, removing from cache")
            del api_key_cache[phone_number]
    return None


def validate_phone_number(phone_number):
    """Validate if the phone number is in the correct format for WhatsApp
    
    Args:
        phone_number (str): The phone number to validate
        
    Returns:
        tuple: (bool, str) - (is_valid, error_message_or_formatted_number)
    """
    if not phone_number:
        return False, "Phone number cannot be empty"
    
    # Remove any spaces, dashes, or + signs
    cleaned = ''.join(filter(str.isdigit, phone_number))
    
    # Check if it has at least 10 digits (most countries have at least 10 digits)
    if len(cleaned) < 10:  # 1234567890 (10 chars minimum)
        return False, f"Phone number {phone_number} is too short. It should include country code and at least 10 digits."
    
    # Composio requires phone numbers WITHOUT the + sign
    logger.info(f"Formatted phone number {phone_number} to {cleaned} for Composio (no + sign)")
    return True, cleaned


def generate_message(prompt):
    """Generate a professional WhatsApp message using Google Gemini
    
    Args:
        prompt (str): The prompt describing what message to generate
        
    Returns:
        dict: Dictionary with success status and generated content
    """
    try:
        # Use the default initialized client
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        detailed_prompt = f"""
        Create a professional WhatsApp message based on this instruction:
        "{prompt}"
        
        The message should be:
        - Clear and concise
        - Professional in tone
        - Well-structured with paragraphs as needed
        - Appropriate for WhatsApp (not too formal, but still professional)
        - Include any important details mentioned in the instruction
        
        Return only the message text, nothing else.
        """
        
        # Generate the response
        response = model.generate_content(detailed_prompt)
        return {
            "success": True,
            "content": response.text
        }
    
    except Exception as e:
        logger.error(f"Error generating message: {str(e)}")
        return {
            "success": False,
            "error": f"Error generating message: {str(e)}"
        }


def send_text_to_whatsapp(message, phone_number, api_key=None, entity_id="default"):
    """Send a text message to WhatsApp using Composio
    
    Args:
        message (str): The message to send
        phone_number (str): The recipient's WhatsApp phone number
        api_key (str, optional): WhatsApp API key. If not provided, will try to use a cached key.
        entity_id (str, optional): The entity ID used to identify which WhatsApp account to use.
                                  Defaults to "default".
    
    Returns:
        dict: Dictionary with success status and response message
    """
    try:
        # Initialize Composio tool set with API key
        composio_tool_set = ComposioToolSet(api_key=COMPOSIO_API_KEY)
        
        # Validate phone number
        is_valid, result = validate_phone_number(phone_number)
        if not is_valid:
            return {
                "success": False,
                "error": result  # This will be the error message
            }
        
        # Use the formatted phone number
        formatted_phone = result
        
        # Add a note about WhatsApp messaging restrictions
        logger.info(f"Sending WhatsApp message to {formatted_phone}. Note: Message will only be delivered if the recipient has messaged you within the last 24 hours or if you're using a template message.")
        
        # Prepare action parameters with the correct parameter names
        # Composio expects 'to_number' and 'text' for WhatsApp messages
        action_params = {
            "to_number": formatted_phone,
            "text": message
        }
        
        # Use the string action name that matches what Composio expects for WhatsApp
        response = composio_tool_set.execute_action(
            "WHATSAPP_SEND_MESSAGE",
            action_params,
            entity_id=entity_id
        )
        
        logger.info(f"Composio response: {response}")
        
        # Check if response is successful by examining its structure and content
        if response:
            # Check for success information in different structures
            if hasattr(response, 'successfull') and response.successfull:
                return {"success": True, "message": f"Message successfully sent to {phone_number}"}
            elif hasattr(response, 'success') and response.success:
                return {"success": True, "message": f"Message successfully sent to {phone_number}"}
            elif hasattr(response, 'data') and response.data:
                return {"success": True, "message": f"Message successfully sent to {phone_number}"}
            elif isinstance(response, dict) and response.get('successfull'):
                return {"success": True, "message": f"Message successfully sent to {phone_number}"}
            elif isinstance(response, dict) and response.get('success'):
                return {"success": True, "message": f"Message successfully sent to {phone_number}"}
            elif isinstance(response, dict) and 'data' in response and response['data']:
                return {"success": True, "message": f"Message successfully sent to {phone_number}"}
        
        # If none of the success checks passed, return error
        error_message = None
        if hasattr(response, 'error'):
            error_message = response.error
        elif isinstance(response, dict) and 'error' in response:
            error_message = response['error']
            
        return {
            "success": False,
            "error": f"Failed to send message via Composio: {error_message or 'Unknown error in response format'}"
        }
    
    except Exception as e:
        logger.error(f"Error using Composio API: {str(e)}")
        return {
            "success": False,
            "error": f"Error using Composio API: {str(e)}"
        }


def send_media_to_whatsapp(media_url, caption, phone_number, api_key=None, entity_id="default"):
    """Send a media message to WhatsApp using Composio
    
    Args:
        media_url (str): The URL of the media to send
        caption (str): The caption for the media
        phone_number (str): The recipient's WhatsApp phone number
        api_key (str, optional): WhatsApp API key. If not provided, will try to use a cached key.
        entity_id (str, optional): The entity ID used to identify which WhatsApp account to use.
                                  Defaults to "default".
    
    Returns:
        dict: Dictionary with success status and response message
    """
    try:
        # Initialize Composio tool set with API key
        composio_tool_set = ComposioToolSet(api_key=COMPOSIO_API_KEY)
        
        # Validate phone number
        is_valid, result = validate_phone_number(phone_number)
        if not is_valid:
            return {
                "success": False,
                "error": result  # This will be the error message
            }
        
        # Use the formatted phone number
        formatted_phone = result
        
        # Add a note about WhatsApp messaging restrictions
        logger.info(f"Sending WhatsApp media to {formatted_phone}. Note: Media will only be delivered if the recipient has messaged you within the last 24 hours or if you're using a template message.")
        
        # Prepare action parameters with the correct parameter names
        # Composio expects 'to_number', 'media_url', and 'caption' for WhatsApp media messages
        action_params = {
            "to_number": formatted_phone,
            "media_url": media_url,
            "caption": caption
        }
        
        # Use the string action name that matches what Composio expects for WhatsApp
        response = composio_tool_set.execute_action(
            "WHATSAPP_SEND_MEDIA",
            action_params,
            entity_id=entity_id
        )
        
        logger.info(f"Composio response: {response}")
        
        # Check if response is successful by examining its structure and content
        if response:
            # Check for success information in different structures
            if hasattr(response, 'successfull') and response.successfull:
                return {"success": True, "message": f"Media successfully sent to {phone_number}"}
            elif hasattr(response, 'success') and response.success:
                return {"success": True, "message": f"Media successfully sent to {phone_number}"}
            elif hasattr(response, 'data') and response.data:
                return {"success": True, "message": f"Media successfully sent to {phone_number}"}
            elif isinstance(response, dict) and response.get('successfull'):
                return {"success": True, "message": f"Media successfully sent to {phone_number}"}
            elif isinstance(response, dict) and response.get('success'):
                return {"success": True, "message": f"Media successfully sent to {phone_number}"}
            elif isinstance(response, dict) and 'data' in response and response['data']:
                return {"success": True, "message": f"Media successfully sent to {phone_number}"}
        
        # If none of the success checks passed, return error
        error_message = None
        if hasattr(response, 'error'):
            error_message = response.error
        elif isinstance(response, dict) and 'error' in response:
            error_message = response['error']
            
        return {
            "success": False,
            "error": f"Failed to send media via Composio: {error_message or 'Unknown error in response format'}"
        }
    
    except Exception as e:
        logger.error(f"Error using Composio API: {str(e)}")
        return {
            "success": False,
            "error": f"Error using Composio API: {str(e)}"
        }


def send_template_to_whatsapp(template_name, template_params, phone_number, api_key=None, entity_id="default"):
    """Send a template message to WhatsApp using Composio
    
    Args:
        template_name (str): The name of the template to use
        template_params (dict): Parameters for the template
        phone_number (str): The recipient's WhatsApp phone number
        api_key (str, optional): WhatsApp API key. If not provided, will try to use a cached key.
        entity_id (str, optional): The entity ID used to identify which WhatsApp account to use.
                                  Defaults to "default".
    
    Returns:
        dict: Dictionary with success status and response message
    """
    try:
        # Initialize Composio tool set with API key
        composio_tool_set = ComposioToolSet(api_key=COMPOSIO_API_KEY)
        
        # Validate phone number
        is_valid, result = validate_phone_number(phone_number)
        if not is_valid:
            return {
                "success": False,
                "error": result  # This will be the error message
            }
        
        # Use the formatted phone number
        formatted_phone = result
        
        # Add a note about template messages
        logger.info(f"Sending WhatsApp template message to {formatted_phone}. Template messages can be sent to any opted-in user, regardless of the 24-hour window.")
        
        # Prepare action parameters with the correct parameter names
        # Composio expects 'to_number', 'template_name', and 'template_params' for WhatsApp template messages
        action_params = {
            "to_number": formatted_phone,
            "template_name": template_name,
            "template_params": template_params
        }
        
        # Use the string action name that matches what Composio expects for WhatsApp
        response = composio_tool_set.execute_action(
            "WHATSAPP_SEND_TEMPLATE_MESSAGE",
            action_params,
            entity_id=entity_id
        )
        
        logger.info(f"Composio response: {response}")
        
        # Check if response is successful by examining its structure and content
        if response:
            # Check for success information in different structures
            if hasattr(response, 'successfull') and response.successfull:
                return {"success": True, "message": f"Template message successfully sent to {phone_number}"}
            elif hasattr(response, 'success') and response.success:
                return {"success": True, "message": f"Template message successfully sent to {phone_number}"}
            elif hasattr(response, 'data') and response.data:
                return {"success": True, "message": f"Template message successfully sent to {phone_number}"}
            elif isinstance(response, dict) and response.get('successfull'):
                return {"success": True, "message": f"Template message successfully sent to {phone_number}"}
            elif isinstance(response, dict) and response.get('success'):
                return {"success": True, "message": f"Template message successfully sent to {phone_number}"}
            elif isinstance(response, dict) and 'data' in response and response['data']:
                return {"success": True, "message": f"Template message successfully sent to {phone_number}"}
        
        # If none of the success checks passed, return error
        error_message = None
        if hasattr(response, 'error'):
            error_message = response.error
        elif isinstance(response, dict) and 'error' in response:
            error_message = response['error']
            
        return {
            "success": False,
            "error": f"Failed to send template message via Composio: {error_message or 'Unknown error in response format'}"
        }
    
    except Exception as e:
        logger.error(f"Error using Composio API: {str(e)}")
        return {
            "success": False,
            "error": f"Error using Composio API: {str(e)}"
        }


def send_to_whatsapp(message, phone_number, message_type="text", media_url=None, template_name=None, 
                    template_params=None, api_key=None, entity_id="default"):
    """Send a message to WhatsApp using Composio
    
    Args:
        message (str): The message to send (for text messages) or caption (for media messages)
        phone_number (str): The recipient's WhatsApp phone number
        message_type (str, optional): Type of message to send: "text", "media", or "template". Defaults to "text".
        media_url (str, optional): URL of media to send. Required for media messages.
        template_name (str, optional): Name of template to use. Required for template messages.
        template_params (dict, optional): Parameters for the template. Required for template messages.
        api_key (str, optional): WhatsApp API key. If not provided, will try to use a cached key.
        entity_id (str, optional): The entity ID used to identify which WhatsApp account to use.
                                  Defaults to "default".
    
    Returns:
        dict: Dictionary with success status and response message
    """
    try:
        # Validate required parameters
        if not phone_number:
            return {
                "success": False,
                "error": "Phone number is required"
            }
        
        # Try to get a cached API key if none is provided
        actual_api_key = api_key
        if not actual_api_key or actual_api_key == "string":
            actual_api_key = get_api_key_for_phone(phone_number)
            if actual_api_key:
                logger.info(f"Using cached API key for phone number {phone_number}")
            else:
                # For WhatsApp, we can continue without an API key since we're using the Composio API key
                logger.info("No API key provided or found in cache. Using default Composio API key.")
        else:
            # If a valid API key was provided, store it for future use
            store_api_key_for_phone(phone_number, actual_api_key)
        
        # Send message based on type
        if message_type == "text":
            logger.info(f"Sending text message to {phone_number}")
            return send_text_to_whatsapp(message, phone_number, actual_api_key, entity_id)
        elif message_type == "media":
            if not media_url:
                return {
                    "success": False,
                    "error": "Media URL is required for media messages"
                }
            logger.info(f"Sending media message to {phone_number}")
            return send_media_to_whatsapp(media_url, message, phone_number, actual_api_key, entity_id)
        elif message_type == "template":
            if not template_name or not template_params:
                return {
                    "success": False,
                    "error": "Template name and parameters are required for template messages"
                }
            logger.info(f"Sending template message to {phone_number}")
            return send_template_to_whatsapp(template_name, template_params, phone_number, actual_api_key, entity_id)
        else:
            return {
                "success": False,
                "error": f"Invalid message type: {message_type}. Must be one of: text, media, template"
            }
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return {
            "success": False,
            "error": f"Error sending message: {str(e)}"
        }
