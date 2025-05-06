import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(log_dir="logs"):
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Console handler
            logging.StreamHandler(),
            # File handler with rotation
            RotatingFileHandler(
                os.path.join(log_dir, 'app.log'),
                maxBytes=10485760,  # 10MB
                backupCount=5
            )
        ]
    )
    
    # Set specific levels for some loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    
    # Return root logger
    return logging.getLogger()
