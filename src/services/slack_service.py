import os
import logging
import google.generativeai as genai
from composio_openai import ComposioToolSet, Action
from src.config.settings import GEMINI_API_KEY, COMPOSIO_API_KEY, SLACK_CHANNELS

# Configure logging
logger = logging.getLogger("slack_service")

# Initialize Google Gemini API client
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Composio tool set
composio_tool_set = ComposioToolSet(api_key=COMPOSIO_API_KEY)


def setup_slack_integration():
    """Setup Slack integration if not already done"""
    try:
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


def get_channels():
    """Return available Slack channels"""
    channels = []
    for key, channel in SLACK_CHANNELS.items():
        channels.append({
            "id": channel["id"],
            "name": channel["name"]
        })
    return channels


def get_channel_name(channel_id):
    """Get channel name from channel ID"""
    for key, channel in SLACK_CHANNELS.items():
        if channel["id"] == channel_id:
            return channel["name"]
    return "unknown-channel"


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


def send_to_slack_composio(message, channel_id):
    """Send the message to Slack using Composio"""
    try:
        # Add debug logging to see the full parameters
        debug_params = {
            "channel_id": channel_id,
            "message": message
        }
        logger.info(f"Sending with parameters: {debug_params}")
        
        # Use the string action name that matches what Composio expects for Slack
        response = composio_tool_set.execute_action(
            "SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL",
            {
                "channel": channel_id,
                "text": message
            }
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


def send_to_slack(message, channel_id):
    """Send the message to Slack using Composio"""
    try:
        logger.info(f"Sending message to channel {channel_id}")
        response = send_to_slack_composio(message, channel_id)
        
        return response
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return {
            "success": False,
            "error": f"Error sending message: {str(e)}"
        }
