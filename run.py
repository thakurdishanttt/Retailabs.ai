import uvicorn
import os
from src.utils.logging_config import setup_logging

# Setup logging
logger = setup_logging()

if __name__ == "__main__":
    logger.info("Starting Retailabs AI Agents API server...")
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    
    # Run the server
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
