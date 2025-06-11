#!/usr/bin/env python3
"""
Startup script for PropMatch backend
Handles database initialization, migration, and health checks
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings, validate_settings
from app.db.database import test_connection, create_tables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main startup function"""
    
    logger.info("🚀 Starting PropMatch backend initialization...")
    
    try:
        # Step 1: Validate environment variables
        logger.info("📋 Validating environment variables...")
        validate_settings()
        logger.info("✅ Environment variables validated")
        
        # Step 2: Test database connection (skip if development mode)
        if settings.SKIP_DB_CONNECTION:
            logger.info("⚠️  Skipping database connection (development mode)")
        else:
            logger.info("🔌 Testing database connection...")
            if not test_connection():
                logger.error("❌ Database connection failed")
                sys.exit(1)
            logger.info("✅ Database connection successful")
            
            # Step 3: Create database tables (if needed)
            logger.info("📊 Creating database tables...")
            create_tables()
            logger.info("✅ Database tables created/verified")
            
            # Step 4: Check existing property data
            from app.db.database import SessionLocal, PropertyDB
            db = SessionLocal()
            property_count = db.query(PropertyDB).count()
            db.close()
            
            logger.info(f"📈 Found {property_count} properties in database")
            
            if property_count == 0:
                logger.warning("⚠️  No properties found in database")
                logger.info("💡 Make sure your Supabase database has the property data")
                logger.info("🔧 You may need to manually migrate your CSV data to Supabase")
            else:
                logger.info(f"✅ Database ready with {property_count} properties")
        
        # Step 5: Verify API keys (optional for Phase 1)
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
            logger.info("🤖 OpenAI API key configured")
        else:
            logger.info("⚠️  OpenAI API key not configured (needed for Phase 2)")
        
        if settings.PINECONE_API_KEY and settings.PINECONE_API_KEY != "your_pinecone_api_key_here":
            logger.info("🔍 Pinecone API key configured")
        else:
            logger.info("⚠️  Pinecone API key not configured (needed for Phase 2)")
        
        if settings.REDIS_URL and not settings.REDIS_URL.startswith("redis://localhost"):
            logger.info("🗄️  Redis Cloud URL configured")
        else:
            logger.info("⚠️  Redis Cloud URL not configured (needed for Phase 3)")
        
        logger.info("🎉 PropMatch backend initialization completed successfully!")
        logger.info("🌐 Ready to start the API server")
        
    except Exception as e:
        logger.error(f"💥 Initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 