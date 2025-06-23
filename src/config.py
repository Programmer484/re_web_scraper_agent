"""Configuration constants for Zillow-Agent"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Apify configuration
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
ZILLOW_ACTOR_ID = "maxcopell/zillow-scraper"

# Result thresholds
MAX_RESULTS = 500
