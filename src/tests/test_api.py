import requests
import logging
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api_tests")

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_health_endpoint():
    """Test the health endpoint"""
    logger.info("Testing health endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Health endpoint response: {data}")
        
        assert data["status"] == "healthy", "Health status should be 'healthy'"
        logger.info("✅ Health endpoint test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Health endpoint test failed: {str(e)}")
        return False

def test_detailed_health_endpoint():
    """Test the detailed health endpoint"""
    logger.info("Testing detailed health endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/health/detailed")
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Detailed health endpoint response: {data}")
        
        assert "api_connections" in data, "Response should include API connections"
        logger.info("✅ Detailed health endpoint test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Detailed health endpoint test failed: {str(e)}")
        return False

def test_slack_channels_endpoint():
    """Test the Slack channels endpoint"""
    logger.info("Testing Slack channels endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/slack/channels")
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Slack channels endpoint response: {data}")
        
        assert "channels" in data, "Response should include channels list"
        logger.info("✅ Slack channels endpoint test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Slack channels endpoint test failed: {str(e)}")
        return False

def test_generate_email_endpoint():
    """Test the generate email endpoint"""
    logger.info("Testing generate email endpoint...")
    
    try:
        payload = {
            "recipient_email": "test@example.com",
            "subject": "Test Email",
            "content_prompt": "Write a test email to verify the API is working",
            "is_formal": True
        }
        
        response = requests.post(f"{BASE_URL}/gmail/generate", json=payload)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Generate email endpoint response: {data}")
        
        assert data["success"] is True, "Email generation should succeed"
        assert data["email_content"] is not None, "Email content should not be None"
        logger.info("✅ Generate email endpoint test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Generate email endpoint test failed: {str(e)}")
        return False

def test_generate_slack_message_endpoint():
    """Test the generate Slack message endpoint"""
    logger.info("Testing generate Slack message endpoint...")
    
    try:
        # Get available channels first
        channels_response = requests.get(f"{BASE_URL}/slack/channels")
        channels_response.raise_for_status()
        
        channels_data = channels_response.json()
        
        if not channels_data["channels"]:
            logger.warning("No Slack channels available for testing")
            return False
        
        # Use the first available channel
        channel_id = channels_data["channels"][0]["id"]
        
        payload = {
            "content_prompt": "Write a test message to verify the API is working",
            "channel_id": channel_id
        }
        
        response = requests.post(f"{BASE_URL}/slack/generate", json=payload)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Generate Slack message endpoint response: {data}")
        
        assert data["success"] is True, "Slack message generation should succeed"
        assert data["message_content"] is not None, "Message content should not be None"
        logger.info("✅ Generate Slack message endpoint test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Generate Slack message endpoint test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all API tests"""
    logger.info("Starting API tests...")
    
    # Test results
    results = {
        "health": test_health_endpoint(),
        "detailed_health": test_detailed_health_endpoint(),
        "slack_channels": test_slack_channels_endpoint(),
        "generate_email": test_generate_email_endpoint(),
        "generate_slack_message": test_generate_slack_message_endpoint()
    }
    
    # Print summary
    logger.info("\n--- Test Results Summary ---")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
