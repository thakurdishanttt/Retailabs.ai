import os
import logging
import google.generativeai as genai
from composio_openai import ComposioToolSet, Action
from src.config.settings import GEMINI_API_KEY, COMPOSIO_API_KEY
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Configure logging
logger = logging.getLogger("linkedin_service")

# Initialize Google Gemini API client
genai.configure(api_key=GEMINI_API_KEY)

# Token cache to store valid access tokens
# Format: {entity_id: {"token": "access_token", "expires": datetime}}
token_cache = {}


def setup_linkedin_integration():
    """Setup LinkedIn integration if not already done"""
    try:
        # Always use the Composio API key from settings for setup
        composio_tool_set = ComposioToolSet(api_key=COMPOSIO_API_KEY)
        
        # Initiate connection to LinkedIn
        response = composio_tool_set.initiate_connection(
            app="LINKEDIN",
            entity_id="default"
        )
        
        # Access properties directly instead of using .get()
        if response and hasattr(response, 'redirectUrl'):
            logger.info("LinkedIn authentication URL generated")
            return {
                "success": True,
                "redirect_url": response.redirectUrl,
                "message": "Please complete LinkedIn authentication by opening this URL in your browser"
            }
            
            # Check if connection is active
            if hasattr(response, 'connectedAccountId'):
                connection = composio_tool_set.get_connected_account(
                    id=response.connectedAccountId
                )
                # Check status directly as property
                if connection and hasattr(connection, 'status') and connection.status == "ACTIVE":
                    logger.info("LinkedIn connection is active")
                    return {
                        "success": True,
                        "message": "LinkedIn connection is active"
                    }
        
        return {
            "success": False,
            "message": "Failed to setup LinkedIn integration"
        }
        
    except Exception as e:
        logger.error(f"Error setting up LinkedIn integration: {str(e)}")
        return {
            "success": False,
            "message": f"Error setting up LinkedIn integration: {str(e)}"
        }


def store_token_for_entity(entity_id, access_token):
    """Store an access token for a specific entity ID
    
    Args:
        entity_id (str): The entity ID
        access_token (str): The LinkedIn access token to store
    """
    if entity_id and access_token and access_token != "string":
        # Store the token with a 24-hour expiration
        token_cache[entity_id] = {
            "token": access_token,
            "expires": datetime.now() + timedelta(hours=24)
        }
        logger.info(f"Stored token for entity {entity_id}")


def get_token_for_entity(entity_id):
    """Get a stored access token for a specific entity ID
    
    Args:
        entity_id (str): The entity ID
        
    Returns:
        str or None: The stored access token, or None if not found or expired
    """
    if entity_id in token_cache:
        cache_entry = token_cache[entity_id]
        # Check if the token is still valid
        if cache_entry["expires"] > datetime.now():
            logger.info(f"Using cached token for entity {entity_id}")
            return cache_entry["token"]
        else:
            # Token expired, remove it from cache
            logger.info(f"Token for entity {entity_id} expired, removing from cache")
            del token_cache[entity_id]
    return None


def search_profiles(keywords, access_token, limit=10, entity_id="default"):
    """Search for LinkedIn profiles based on keywords
    
    Args:
        keywords (str): Search keywords
        access_token (str): LinkedIn access token
        limit (int): Maximum number of results to return
        entity_id (str): Entity ID for token caching
        
    Returns:
        dict: Search results with success status and profile data
    """
    try:
        # Validate access token
        if not access_token or access_token == "string":
            logger.error("Invalid access token provided to search_profiles")
            return {
                "success": False,
                "error": "Invalid access token provided"
            }
            
        # Store the token for future use
        store_token_for_entity(entity_id, access_token)
        
        # Initialize Composio tool set with the provided API key
        composio_tool_set = ComposioToolSet(api_key=COMPOSIO_API_KEY)
        
        # Prepare parameters for the LinkedIn search action
        search_params = {
            "keywords": keywords,
            "limit": limit,
            "token": access_token
        }
        
        # Execute the LinkedIn search action
        # Try different action names that might be available in Composio
        try:
            response = composio_tool_set.execute_action(
                "LINKEDIN_SEARCH_FOR_PEOPLE",  # First attempt with this action name
                search_params
            )
        except Exception as action_error:
            logger.warning(f"First action attempt failed: {str(action_error)}")
            try:
                # Second attempt with alternative action name
                response = composio_tool_set.execute_action(
                    "LINKEDIN_SEARCHES_FOR_PEOPLE",
                    search_params
                )
            except Exception as alt_error:
                logger.warning(f"Second action attempt failed: {str(alt_error)}")
                # Final fallback to a generic search action
                response = composio_tool_set.execute_action(
                    "LINKEDIN_SEARCHES_PROFILES",
                    search_params
                )
        
        # Process and format the response
        if response and hasattr(response, 'data') and response.data:
            profiles = []
            for profile in response.data:
                profile_info = {
                    "id": profile.id,
                    "name": profile.name,
                    "headline": getattr(profile, 'headline', None),
                    "url": getattr(profile, 'profileUrl', None)
                }
                profiles.append(profile_info)
                
            return {
                "success": True,
                "message": f"Found {len(profiles)} profiles matching your search",
                "profiles": profiles
            }
        
        # Handle error cases
        error_message = None
        if hasattr(response, 'error'):
            error_message = response.error
        elif isinstance(response, dict) and 'error' in response:
            error_message = response['error']
            
        return {
            "success": False,
            "error": f"Failed to search LinkedIn profiles: {error_message or 'No profiles found'}"
        }
        
    except Exception as e:
        logger.error(f"Error searching LinkedIn profiles: {str(e)}")
        return {
            "success": False,
            "error": f"Error searching LinkedIn profiles: {str(e)}"
        }


def send_connection_request(profile_url, message, access_token, entity_id="default"):
    """Send a LinkedIn connection request
    
    Args:
        profile_url (str): URL of the LinkedIn profile to connect with
        message (str): Optional personalized message for the connection request
        access_token (str): LinkedIn access token
        entity_id (str): Entity ID for token caching
        
    Returns:
        dict: Result with success status and message
    """
    try:
        # Validate access token
        if not access_token or access_token == "string":
            logger.error("Invalid access token provided to send_connection_request")
            return {
                "success": False,
                "error": "Invalid access token provided"
            }
            
        # Store the token for future use
        store_token_for_entity(entity_id, access_token)
        
        # Initialize Composio tool set with the provided API key
        composio_tool_set = ComposioToolSet(api_key=COMPOSIO_API_KEY)
        
        # Prepare parameters for the LinkedIn connection request action
        connection_params = {
            "profileUrl": profile_url,
            "message": message if message else "I'd like to connect with you on LinkedIn.",
            "token": access_token
        }
        
        # Execute the LinkedIn connection request action
        try:
            response = composio_tool_set.execute_action(
                "LINKEDIN_SENDS_CONNECTION_REQUEST",  # First attempt
                connection_params
            )
        except Exception as action_error:
            logger.warning(f"First action attempt failed: {str(action_error)}")
            try:
                # Second attempt with alternative action name
                response = composio_tool_set.execute_action(
                    "LINKEDIN_SENDS_A_CONNECTION_REQUEST",
                    connection_params
                )
            except Exception as alt_error:
                logger.warning(f"Second action attempt failed: {str(alt_error)}")
                # Final fallback
                response = composio_tool_set.execute_action(
                    "LINKEDIN_CONNECT_WITH_PROFILE",
                    connection_params
                )
        
        # Process the response
        if response:
            # Check for success information in different structures
            if hasattr(response, 'successfull') and response.successfull:
                return {"success": True, "message": "Connection request sent successfully"}
            elif hasattr(response, 'success') and response.success:
                return {"success": True, "message": "Connection request sent successfully"}
            elif hasattr(response, 'data') and response.data:
                return {"success": True, "message": "Connection request sent successfully"}
        
        # Handle error cases
        error_message = None
        if hasattr(response, 'error'):
            error_message = response.error
        elif isinstance(response, dict) and 'error' in response:
            error_message = response['error']
            
        return {
            "success": False,
            "error": f"Failed to send connection request: {error_message or 'Unknown error'}"
        }
        
    except Exception as e:
        logger.error(f"Error sending connection request: {str(e)}")
        return {
            "success": False,
            "error": f"Error sending connection request: {str(e)}"
        }


def generate_message(prompt):
    """Generate a professional LinkedIn message using Google Gemini
    
    Args:
        prompt (str): Prompt describing the message to generate
        
    Returns:
        dict: Generated message content or error
    """
    try:
        # Enhance the prompt for better LinkedIn-specific content
        enhanced_prompt = f"""
        Create a professional LinkedIn message based on the following prompt:
        
        {prompt}
        
        The message should be:
        1. Professional and appropriate for LinkedIn
        2. Concise (under 300 characters for connection requests, under 1000 for messages)
        3. Personalized and engaging
        4. Free of hashtags unless specifically requested
        5. Include a clear call to action when appropriate
        
        Message:
        """
        
        # Generate content using Gemini
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(enhanced_prompt)
        
        # Extract and clean the generated text
        if response and hasattr(response, 'text'):
            generated_text = response.text.strip()
            return {
                "success": True,
                "content": generated_text
            }
        else:
            logger.error("Failed to generate message: Empty response from Gemini")
            return {
                "success": False,
                "error": "Failed to generate message content"
            }
            
    except Exception as e:
        logger.error(f"Error generating message: {str(e)}")
        return {
            "success": False,
            "error": f"Error generating message: {str(e)}"
        }


def send_message(profile_id, message, access_token, entity_id="default"):
    """Send a message to a LinkedIn connection
    
    Args:
        profile_id (str): LinkedIn profile ID to message
        message (str): Message content to send
        access_token (str): LinkedIn access token
        entity_id (str): Entity ID for token caching
        
    Returns:
        dict: Result with success status and message
    """
    try:
        # Validate access token
        if not access_token or access_token == "string":
            logger.error("Invalid access token provided to send_message")
            return {
                "success": False,
                "error": "Invalid access token provided"
            }
            
        # Store the token for future use
        store_token_for_entity(entity_id, access_token)
        
        # Initialize Composio tool set with the provided API key
        composio_tool_set = ComposioToolSet(api_key=COMPOSIO_API_KEY)
        
        # Prepare parameters for the LinkedIn message action
        message_params = {
            "profileId": profile_id,
            "message": message,
            "token": access_token
        }
        
        # Execute the LinkedIn message action
        try:
            response = composio_tool_set.execute_action(
                "LINKEDIN_SENDS_MESSAGE",  # First attempt
                message_params
            )
        except Exception as action_error:
            logger.warning(f"First action attempt failed: {str(action_error)}")
            try:
                # Second attempt with alternative action name
                response = composio_tool_set.execute_action(
                    "LINKEDIN_SENDS_A_MESSAGE",
                    message_params
                )
            except Exception as alt_error:
                logger.warning(f"Second action attempt failed: {str(alt_error)}")
                # Final fallback
                response = composio_tool_set.execute_action(
                    "LINKEDIN_MESSAGE_PROFILE",
                    message_params
                )
        
        # Process the response
        if response:
            # Check for success information in different structures
            if hasattr(response, 'successfull') and response.successfull:
                return {"success": True, "message": "Message sent successfully"}
            elif hasattr(response, 'success') and response.success:
                return {"success": True, "message": "Message sent successfully"}
            elif hasattr(response, 'data') and response.data:
                return {"success": True, "message": "Message sent successfully"}
        
        # Handle error cases
        error_message = None
        if hasattr(response, 'error'):
            error_message = response.error
        elif isinstance(response, dict) and 'error' in response:
            error_message = response['error']
            
        return {
            "success": False,
            "error": f"Failed to send message: {error_message or 'Unknown error'}"
        }
        
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return {
            "success": False,
            "error": f"Error sending message: {str(e)}"
        }


def create_post(content, access_token, image_url=None, article_url=None, entity_id="default"):
    """Create a LinkedIn post
    
    Args:
        content (str): Post content
        access_token (str): LinkedIn access token
        image_url (str, optional): URL of an image to include in the post
        article_url (str, optional): URL of an article to share in the post
        entity_id (str): Entity ID for token caching
        
    Returns:
        dict: Result with success status and message
    """
    try:
        # Validate access token
        if not access_token or access_token == "string":
            logger.error("Invalid access token provided to create_post")
            return {
                "success": False,
                "error": "Invalid access token provided"
            }
            
        # Store the token for future use
        store_token_for_entity(entity_id, access_token)
        
        # Initialize Composio tool set with the provided API key
        composio_tool_set = ComposioToolSet(api_key=COMPOSIO_API_KEY)
        
        # Prepare parameters for the LinkedIn post action
        post_params = {
            "content": content,
            "token": access_token
        }
        
        # Add optional parameters if provided
        if image_url:
            post_params["imageUrl"] = image_url
        if article_url:
            post_params["articleUrl"] = article_url
        
        # Execute the LinkedIn post action
        try:
            response = composio_tool_set.execute_action(
                "LINKEDIN_CREATES_POST",  # First attempt
                post_params
            )
        except Exception as action_error:
            logger.warning(f"First action attempt failed: {str(action_error)}")
            try:
                # Second attempt with alternative action name
                response = composio_tool_set.execute_action(
                    "LINKEDIN_CREATES_A_POST",
                    post_params
                )
            except Exception as alt_error:
                logger.warning(f"Second action attempt failed: {str(alt_error)}")
                # Final fallback
                response = composio_tool_set.execute_action(
                    "LINKEDIN_SHARE_POST",
                    post_params
                )
        
        # Process the response
        if response:
            # Check for success information in different structures
            if hasattr(response, 'successfull') and response.successfull:
                return {"success": True, "message": "Post created successfully"}
            elif hasattr(response, 'success') and response.success:
                return {"success": True, "message": "Post created successfully"}
            elif hasattr(response, 'data') and response.data:
                post_id = getattr(response.data, 'id', None)
                return {
                    "success": True, 
                    "message": "Post created successfully", 
                    "data": {"post_id": post_id}
                }
        
        # Handle error cases
        error_message = None
        if hasattr(response, 'error'):
            error_message = response.error
        elif isinstance(response, dict) and 'error' in response:
            error_message = response['error']
            
        return {
            "success": False,
            "error": f"Failed to create post: {error_message or 'Unknown error'}"
        }
        
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        return {
            "success": False,
            "error": f"Error creating post: {str(e)}"
        }


def list_available_actions():
    """List all available LinkedIn actions from Composio
    
    Returns:
        dict: List of available actions with their descriptions
    """
    try:
        # Initialize Composio tool set with the provided API key
        composio_tool_set = ComposioToolSet(api_key=COMPOSIO_API_KEY)
        
        # Get all available actions
        all_actions = composio_tool_set.list_actions()
        
        # Filter for LinkedIn actions
        linkedin_actions = []
        for action in all_actions:
            if hasattr(action, 'name') and 'LINKEDIN' in action.name:
                action_info = {
                    "name": action.name,
                    "description": getattr(action, 'description', 'No description available')
                }
                linkedin_actions.append(action_info)
        
        return {
            "success": True,
            "message": f"Found {len(linkedin_actions)} LinkedIn actions",
            "actions": linkedin_actions
        }
        
    except Exception as e:
        logger.error(f"Error listing LinkedIn actions: {str(e)}")
        return {
            "success": False,
            "error": f"Error listing LinkedIn actions: {str(e)}"
        }
