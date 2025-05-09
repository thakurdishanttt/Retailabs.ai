import os
import logging
import google.generativeai as genai
from composio_openai import ComposioToolSet, Action
from src.config.settings import GEMINI_API_KEY, COMPOSIO_API_KEY
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger("slack_service")

# Initialize Google Gemini API client
genai.configure(api_key=GEMINI_API_KEY)

# Token cache to store valid bot tokens
# Format: {channel_id: {"token": "bot_token", "expires": datetime}}
token_cache = {}


def setup_slack_integration():
    """Setup Slack integration if not already done"""
    try:
        # Always use the Composio API key from settings for setup
        composio_tool_set = ComposioToolSet(api_key=COMPOSIO_API_KEY)
        
        # Initiate connection to Slack
        response = composio_tool_set.initiate_connection(
            app="SLACK",
            entity_id="default"
        )
        
        # Access properties directly instead of using .get()
        if response and hasattr(response, 'redirectUrl'):
            logger.info("Slack authentication URL generated")
            return {
                "success": True,
                "redirect_url": response.redirectUrl,
                "message": "Please complete Slack authentication by opening this URL in your browser"
            }
            
            # Check if connection is active
            if hasattr(response, 'connectedAccountId'):
                connection = composio_tool_set.get_connected_account(
                    id=response.connectedAccountId
                )
                # Check status directly as property
                if connection and hasattr(connection, 'status') and connection.status == "ACTIVE":
                    logger.info("Slack connection is active")
                    return {
                        "success": True,
                        "message": "Slack connection is active"
                    }
        
        return {
            "success": False,
            "message": "Failed to setup Slack integration"
        }
        
    except Exception as e:
        logger.error(f"Error setting up Slack integration: {str(e)}")
        return {
            "success": False,
            "message": f"Error setting up Slack integration: {str(e)}"
        }


def store_token_for_channel(channel_id, bot_token):
    """Store a bot token for a specific channel ID
    
    Args:
        channel_id (str): The Slack channel ID
        bot_token (str): The Slack bot token to store
    """
    if channel_id and bot_token and bot_token != "string":
        # Store the token with a 24-hour expiration
        token_cache[channel_id] = {
            "token": bot_token,
            "expires": datetime.now() + timedelta(hours=24)
        }
        logger.info(f"Stored token for channel {channel_id}")


def get_token_for_channel(channel_id):
    """Get a stored bot token for a specific channel ID
    
    Args:
        channel_id (str): The Slack channel ID
        
    Returns:
        str or None: The stored bot token, or None if not found or expired
    """
    if channel_id in token_cache:
        cache_entry = token_cache[channel_id]
        # Check if the token is still valid
        if cache_entry["expires"] > datetime.now():
            logger.info(f"Using cached token for channel {channel_id}")
            return cache_entry["token"]
        else:
            # Token expired, remove it from cache
            logger.info(f"Token for channel {channel_id} expired, removing from cache")
            del token_cache[channel_id]
    return None


def get_channels(bot_token):
    """Fetch available Slack channels using the provided bot token
    
    Args:
        bot_token (str): Slack bot token to use for authentication
        
    Returns:
        list: List of channel objects with id and name
    """
    try:
        # Validate bot token
        if not bot_token or bot_token == "string":
            logger.error("Invalid bot token provided to get_channels")
            return []
            
        # Initialize Composio tool set with the API key from settings
        composio_tool_set = ComposioToolSet(api_key=COMPOSIO_API_KEY)
        
        # Use the Slack Web API directly through Composio
        # This is the most reliable method as it doesn't depend on specific Composio action names
        import requests
        import json
        
        # Create a direct HTTP request to the Slack API
        headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Use the conversations.list endpoint which is the current recommended way to list channels
        url = "https://slack.com/api/conversations.list"
        params = {
            "types": "public_channel,private_channel",  # Get both public and private channels
            "exclude_archived": "true",                # Skip archived channels
            "limit": "1000"                            # Get up to 1000 channels
        }
        
        logger.info("Making direct API call to Slack conversations.list endpoint")
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            logger.error(f"Error from Slack API: {response.status_code} - {response.text}")
            return []
            
        # Parse the JSON response
        data = response.json()
        logger.info(f"Slack API response status: {data.get('ok', False)}")
        
        # Check if the request was successful
        if not data.get('ok', False):
            error = data.get('error', 'Unknown error')
            logger.error(f"Slack API error: {error}")
            
            # Provide more helpful error information for common issues
            if error == 'missing_scope':
                logger.error("The bot token is missing required scopes. Make sure your Slack bot has the following scopes: channels:read, groups:read")
                return [{
                    "id": "ERROR",
                    "name": "Bot token missing required scopes: channels:read, groups:read"
                }]
            elif error == 'invalid_auth' or error == 'not_authed':
                logger.error("The bot token is invalid or expired")
                return [{
                    "id": "ERROR",
                    "name": "Invalid or expired bot token"
                }]
            else:
                return [{
                    "id": "ERROR",
                    "name": f"Slack API error: {error}"
                }]
            
        # Extract channels from the response
        channels = []
        channel_list = data.get('channels', [])
        
        logger.info(f"Found {len(channel_list)} channels in Slack API response")
        
        for channel in channel_list:
            if 'id' in channel and 'name' in channel:
                # Store the token for this channel
                store_token_for_channel(channel['id'], bot_token)
                
                channels.append({
                    "id": channel['id'],
                    "name": channel['name']
                })
                
        return channels
        
    except Exception as e:
        logger.error(f"Error fetching channels: {str(e)}")
        return []


def get_channel_name(channel_id):
    """This function is kept for backward compatibility but now returns a placeholder
    
    Args:
        channel_id (str): The Slack channel ID
    """
    return "channel"  # Simple placeholder


def generate_message(prompt):
    """Generate a professional Slack message using Google Gemini"""
    try:
        # Initialize the model - use the latest available model
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Create a detailed prompt
        detailed_prompt = f"""
        Create a professional and friendly Slack message based on this instruction:
        "{prompt}"
        
        The message should be:
        - Clear and concise
        - Professional but conversational in tone
        - Include any important details mentioned in the instruction
        - Formatted appropriately for Slack (can include emojis if suitable)
        
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


def send_to_slack_composio(message, channel_id, bot_token):
    """Send the message to Slack using Composio
    
    Args:
        message (str): The message to send
        channel_id (str): The Slack channel ID
        bot_token (str): Slack bot token from the request
    """
    try:
        # Initialize Composio tool set with the API key from settings
        # We always use the Composio API key from settings for the Composio service itself
        composio_tool_set = ComposioToolSet(api_key=COMPOSIO_API_KEY)
        
        # Validate that bot token is provided
        if not bot_token or bot_token == "string":
            return {
                "success": False,
                "error": "A valid Slack bot token must be provided"
            }
        
        # Add debug logging to see the full parameters
        debug_params = {
            "channel_id": channel_id,
            "message": message[:50] + "..." if len(message) > 50 else message,
            "token_provided": bool(bot_token and bot_token != "string")
        }
        logger.info(f"Sending with parameters: {debug_params}")
        
        # Create the parameters for the Composio action with the required bot token
        action_params = {
            "channel": channel_id,
            "text": message,
            "token": bot_token  # Always use the provided token
        }
            
        # Use the string action name that matches what Composio expects for Slack
        response = composio_tool_set.execute_action(
            "SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL",
            action_params
        )
        
        logger.info(f"Composio response: {response}")
        
        # Check if response is successful by examining its structure and content
        if response:
            # Check for success information in different structures
            if hasattr(response, 'successfull') and response.successfull:
                return {"success": True, "message": f"Message successfully sent to channel"}
            elif hasattr(response, 'success') and response.success:
                return {"success": True, "message": f"Message successfully sent to channel"}
            elif hasattr(response, 'data') and response.data:
                return {"success": True, "message": f"Message successfully sent to channel"}
            elif isinstance(response, dict) and response.get('successfull'):
                return {"success": True, "message": f"Message successfully sent to channel"}
            elif isinstance(response, dict) and response.get('success'):
                return {"success": True, "message": f"Message successfully sent to channel"}
            elif isinstance(response, dict) and 'data' in response and response['data']:
                return {"success": True, "message": f"Message successfully sent to channel"}
        
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


def send_to_slack(message, channel_id=None, channel_name=None, bot_token=None):
    """Send the message to Slack using Composio
    
    Args:
        message (str): The message to send
        channel_id (str, optional): The Slack channel ID. Required.
        channel_name (str, optional): The Slack channel name. Used for logging purposes.
        bot_token (str, optional): Slack bot token. If not provided, will try to use a cached token.
    """
    try:
        # Validate required parameters
        if not channel_id:
            return {
                "success": False,
                "error": "Channel ID is required"
            }
        
        # Try to get a cached token if none is provided
        actual_token = bot_token
        if not actual_token or actual_token == "string":
            actual_token = get_token_for_channel(channel_id)
            if actual_token:
                logger.info(f"Using cached token for channel {channel_id}")
            else:
                return {
                    "success": False,
                    "error": "No valid bot token provided or found in cache. Please provide a bot token or first call the channels endpoint with a valid token."
                }
        else:
            # If a valid token was provided, store it for future use
            store_token_for_channel(channel_id, actual_token)
            
        channel_display = channel_name or channel_id
        logger.info(f"Sending message to channel {channel_display}")
        response = send_to_slack_composio(message, channel_id, actual_token)
        
        return response
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return {
            "success": False,
            "error": f"Error sending message: {str(e)}"
        }
