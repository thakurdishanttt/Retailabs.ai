import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API configuration
API_PREFIX = "/api/v1"
PROJECT_NAME = "Retailabs AI Agents API"
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

# Validate required environment variables
if not all([GEMINI_API_KEY, COMPOSIO_API_KEY]):
    raise EnvironmentError(
        "Missing required environment variables. Please ensure GEMINI_API_KEY and "
        "COMPOSIO_API_KEY are set in your .env file."
    )

# Slack channels configuration
SLACK_CHANNELS = {
    "1": {"name": "team-", "id": "C08QPUC28UA"},
    "2": {"name": "social", "id": "C08Q7F3TGS3"},
    "3": {"name": "new-channel", "id": "C08QQM6MREX"},
}
