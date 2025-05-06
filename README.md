# Retailabs AI Agents API

A professional FastAPI backend implementation for Gmail and Slack AI agents powered by Google Gemini and Composio.

## Overview

This project provides a RESTful API for interacting with AI-powered Gmail and Slack messaging agents. The API allows users to:

- Generate and send AI-crafted emails through Gmail integration
- Generate and send AI-crafted messages to Slack channels
- Manage Gmail and Slack integrations through Composio
- Robust error handling and authentication flow

## Project Structure

```bash
src/
├── api/                # API routes and endpoints
│   ├── gmail_routes.py # Gmail-related endpoints
│   ├── slack_routes.py # Slack-related endpoints
│   └── router.py       # Main API router
├── config/             # Configuration settings
│   └── settings.py     # Environment variables and app settings
├── models/             # Data models and schemas
│   └── schemas.py      # Pydantic models for request/response validation
├── services/           # Business logic and external service integrations
│   ├── gmail_service.py # Gmail integration logic
│   └── slack_service.py # Slack integration logic
└── utils/              # Utility functions and helpers
    └── logging_config.py # Logging configuration
```

## API Endpoints

### Gmail Endpoints

- `POST /api/v1/gmail/setup` - Setup Gmail integration with Composio (returns authentication URL)
- `POST /api/v1/gmail/generate` - Generate an AI-crafted email without sending
- `POST /api/v1/gmail/send` - Generate and send an AI-crafted email

### Slack Endpoints

- `POST /api/v1/slack/setup` - Setup Slack integration with Composio (returns authentication URL)
- `GET /api/v1/slack/channels` - Get available Slack channels
- `POST /api/v1/slack/generate` - Generate an AI-crafted Slack message without sending
- `POST /api/v1/slack/send` - Generate and send an AI-crafted Slack message

## Implementation Details

### AI Message Generation

This API uses Google's Gemini 1.5 Pro model to generate contextually appropriate, professional messages for both email and Slack communications. The generation process:

1. Takes a user prompt describing the message content
2. Formats it with appropriate tone and structure
3. Returns a well-crafted message ready for sending

### Composio Integration

The API leverages Composio to handle authentication and communication with Gmail and Slack:

1. User initiates setup through the `/setup` endpoints
2. Composio provides an authentication URL for the respective service
3. After authentication, the API can send messages through the authenticated service
4. Comprehensive error handling ensures reliable operation

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Required API keys
GEMINI_API_KEY=your_gemini_api_key
COMPOSIO_API_KEY=your_composio_api_key

# Optional (only needed if not using Composio for direct Slack API access)
# SLACK_BOT_TOKEN=your_slack_bot_token

# Application settings
DEBUG=False
```

**Note:** The current implementation uses Composio for both Gmail and Slack integration, so the `SLACK_BOT_TOKEN` is not required.

## Running the Application

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the FastAPI application:

   ```bash
   python -m src.main
   ```

3. Access the API documentation:
   - Swagger UI: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
   - ReDoc: [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)

## Development

For development mode with auto-reload:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Standalone Scripts

The repository includes standalone scripts for testing Gmail and Slack functionality outside of the API:

- `gmil_basic.py` - CLI tool for composing and sending emails through Gmail
- `slack_message_agent.py` - CLI tool for composing and sending messages to Slack channels

These scripts are primarily for development and testing purposes and are not part of the production API. They are excluded from version control via the `.gitignore` file.
