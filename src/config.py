"""Configuration constants for Zillow-Agent"""

import os
import logging
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Apify configuration
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
ZILLOW_ACTOR_ID = "maxcopell/zillow-scraper"

# Result thresholds
MAX_RESULTS = 500

# Logging configuration
def setup_logging():
    """Configure comprehensive logging for the application"""
    
    # Set log level directly in config for consistent DEBUG logging
    log_level = "DEBUG"
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[
            # Console handler for immediate feedback
            logging.StreamHandler(sys.stdout),
            # File handler for persistent logs
            logging.FileHandler(f"logs/property_search_{datetime.now().strftime('%Y%m%d')}.log"),
        ]
    )
    
    # Create logger for the application
    logger = logging.getLogger("PropertySearchAgent")
    logger.setLevel(getattr(logging, log_level))
    
    # Also configure uvicorn logger for API requests
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.setLevel(logging.DEBUG)
    
    # Suppress verbose logging from APIFY and HTTP libraries
    logging.getLogger('apify_client').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger.debug("Logging configuration initialized")
    logger.debug(f"Log level set to: {log_level}")
    logger.debug(f"APIFY_TOKEN configured: {'Yes' if APIFY_TOKEN else 'No'}")
    
    return logger

# Initialize logging when module is imported
logger = setup_logging()
