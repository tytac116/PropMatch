from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # FastAPI settings
    PROJECT_NAME: str = "PropMatch API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    # TODO: Add your Supabase database URL here
    # Format: postgresql://postgres:PASSWORD@HOST:5432/postgres
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:password@localhost:5432/propmatch"
    )
    
    # Supabase API settings (alternative to direct PostgreSQL)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    
    # Development settings
    SKIP_DB_CONNECTION: bool = os.getenv("SKIP_DB_CONNECTION", "false").lower() == "true"
    
    # OpenAI API settings
    # TODO: Get your OpenAI API key from https://platform.openai.com/api-keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o-mini"  # Cost-effective for explanations
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # Cost-effective for embeddings
    
    # LangSmith settings for tracing
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "PropMatch-Backend")
    
    # Pinecone settings
    # TODO: Get your Pinecone API key from https://app.pinecone.io/
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    # Environment is optional when using LangChain with Pinecone
    PINECONE_ENVIRONMENT: Optional[str] = os.getenv("PINECONE_ENVIRONMENT", None)
    PINECONE_INDEX_NAME: str = "propmatch-properties"
    
    # Redis settings (for caching) - Using Redis Cloud
    # TODO: Get your Redis URL from Redis Cloud
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "https://your-frontend-domain.vercel.app"
    ]
    
    # Application settings
    MAX_SEARCH_RESULTS: int = 50
    DEFAULT_PAGE_SIZE: int = 20
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"  # Allow extra fields from environment
    )

# Create global settings instance
settings = Settings()

# Validation function to check required environment variables
def validate_settings():
    """Validate that all required environment variables are set"""
    required_vars = []
    
    # Check if we have either PostgreSQL or Supabase credentials
    has_postgres = settings.DATABASE_URL and not settings.SKIP_DB_CONNECTION
    has_supabase = settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY
    
    if not has_postgres and not has_supabase and not settings.SKIP_DB_CONNECTION:
        required_vars.append("DATABASE_URL or (SUPABASE_URL + SUPABASE_ANON_KEY)")
    
    # Only require OpenAI key if we're not in a minimal setup
    if settings.OPENAI_API_KEY:
        logger_info = True  # We have OpenAI configured
    
    missing_vars = []
    for var_name in required_vars:
        missing_vars.append(var_name)
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            f"Please check your .env file and ensure these variables are set."
        )
    
    return True 