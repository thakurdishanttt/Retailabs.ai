import os
import logging
from typing import Dict, Any, Tuple, Optional
import requests
from src.config.settings import GEMINI_API_KEY, COMPOSIO_API_KEY, SLACK_BOT_TOKEN

logger = logging.getLogger(__name__)

def validate_api_keys() -> Tuple[bool, Optional[str]]:
    """
    Validate that all required API keys are present
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    missing_keys = []
    
    if not GEMINI_API_KEY:
        missing_keys.append("GEMINI_API_KEY")
    
    if not COMPOSIO_API_KEY:
        missing_keys.append("COMPOSIO_API_KEY")
    
    # Slack token is optional for Gmail-only operations
    if not SLACK_BOT_TOKEN:
        logger.warning("SLACK_BOT_TOKEN is not set. Slack functionality will be limited.")
    
    if missing_keys:
        error_message = f"Missing required API keys: {', '.join(missing_keys)}"
        return False, error_message
    
    return True, None


def test_gemini_connection() -> Dict[str, Any]:
    """
    Test connection to Google Gemini API
    
    Returns:
        Dictionary with connection status
    """
    import google.generativeai as genai
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        models = genai.list_models()
        
        # Check if we got a valid response
        if models and len(models) > 0:
            return {
                "success": True,
                "message": "Successfully connected to Google Gemini API",
                "models_available": len(models)
            }
        else:
            return {
                "success": False,
                "error": "No models available from Google Gemini API"
            }
    
    except Exception as e:
        logger.error(f"Error connecting to Google Gemini API: {str(e)}")
        return {
            "success": False,
            "error": f"Error connecting to Google Gemini API: {str(e)}"
        }


def test_slack_connection() -> Dict[str, Any]:
    """
    Test connection to Slack API
    
    Returns:
        Dictionary with connection status
    """
    if not SLACK_BOT_TOKEN:
        return {
            "success": False,
            "error": "SLACK_BOT_TOKEN is not set"
        }
    
    try:
        # Test auth with Slack API
        response = requests.post(
            "https://slack.com/api/auth.test",
            headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
        )
        
        result = response.json()
        
        if result.get("ok"):
            return {
                "success": True,
                "message": "Successfully connected to Slack API",
                "bot_name": result.get("user"),
                "team": result.get("team")
            }
        else:
            return {
                "success": False,
                "error": f"Slack API error: {result.get('error', 'Unknown error')}"
            }
    
    except Exception as e:
        logger.error(f"Error connecting to Slack API: {str(e)}")
        return {
            "success": False,
            "error": f"Error connecting to Slack API: {str(e)}"
        }
