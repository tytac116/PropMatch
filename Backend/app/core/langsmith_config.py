"""
LangSmith configuration and initialization
"""

import logging
import os
from app.core.config import settings

logger = logging.getLogger(__name__)

def initialize_langsmith():
    """Initialize LangSmith tracing if enabled and API key is available"""
    
    try:
        if settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY:
            # Set environment variables for LangSmith
            os.environ["LANGSMITH_TRACING"] = "true"
            os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
            os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
            
            logger.info(f"🔍 LangSmith tracing initialized for project: {settings.LANGSMITH_PROJECT}")
            return True
        else:
            logger.info("📊 LangSmith tracing disabled (set LANGSMITH_TRACING=true and LANGSMITH_API_KEY to enable)")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize LangSmith: {e}")
        return False

def get_langsmith_status():
    """Get current LangSmith configuration status"""
    return {
        "enabled": settings.LANGSMITH_TRACING and bool(settings.LANGSMITH_API_KEY),
        "project": settings.LANGSMITH_PROJECT,
        "api_key_configured": bool(settings.LANGSMITH_API_KEY)
    } 