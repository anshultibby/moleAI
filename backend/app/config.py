"""
Configuration module for MoleAI Backend
Centralized loading of environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Required API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")

# Google Custom Search
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# Optional API Keys
JINA_API_KEY = os.getenv("JINA_API_KEY")
RYE_API_KEY = os.getenv("RYE_API_KEY")
RYE_SHOPPER_IP = os.getenv("RYE_SHOPPER_IP", "127.0.0.1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SCRAPFLY_API_KEY = os.getenv("SCRAPFLY_API_KEY")

# Environment Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3005")
NODE_ENV = os.getenv("NODE_ENV", "development")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Validation for required keys
def validate_required_keys():
    """Validate that required API keys are present"""
    required_keys = {
        "GEMINI_API_KEY": GEMINI_API_KEY,
    }
    
    missing_keys = [key for key, value in required_keys.items() if not value]
    
    if missing_keys:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_keys)}. "
            f"Please check your .env file in the backend directory."
        )

# Optional: Auto-validate on import (uncomment if you want strict validation)
# validate_required_keys()

def get_api_key(key_name: str) -> str:
    """Get an API key with validation"""
    key_value = globals().get(key_name)
    if not key_value:
        raise ValueError(f"{key_name} not found in environment variables")
    return key_value

def is_development() -> bool:
    """Check if running in development mode"""
    return ENVIRONMENT == "development" or NODE_ENV == "development"

def is_production() -> bool:
    """Check if running in production mode"""
    return ENVIRONMENT == "production" or NODE_ENV == "production" 