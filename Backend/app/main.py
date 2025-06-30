from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import uvicorn
import os
import logging
from dotenv import load_dotenv

from app.api.routes import properties, search
from app.api.v1 import test_endpoints, hybrid_test_endpoints, explanation_endpoints, security_endpoints
from app.core.config import settings
from app.core.langsmith_config import initialize_langsmith, get_langsmith_status
from app.core.security import (
    limiter, 
    security_middleware, 
    custom_rate_limit_handler,
    rate_limit_general
)

# Load environment variables
load_dotenv()

# Initialize LangSmith tracing
initialize_langsmith()

# Configure logging to show only important information
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Set specific loggers for important information
search_logger = logging.getLogger('search')
search_logger.setLevel(logging.INFO)

security_logger = logging.getLogger('security')
security_logger.setLevel(logging.WARNING)

# Reduce noise from external libraries
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
logging.getLogger('pinecone_plugin_interface').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)

# Create FastAPI app
app = FastAPI(
    title="PropMatch API",
    description="AI-powered property search and matching API with advanced security",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# Security middleware - FIRST (most important)
@app.middleware("http")
async def security_middleware_handler(request: Request, call_next):
    """Apply security checks to all requests"""
    # Skip security checks for health endpoints and docs
    if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
        response = await call_next(request)
        return response
    
    # Apply security checks
    security_result = await security_middleware.security_check(request)
    if security_result:
        return security_result
    
    response = await call_next(request)
    return response

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "propmatch.onrender.com", "*"]  # Allow Render domain
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "https://propmatchai.vercel.app",  # Your actual Vercel domain
        "https://propmatch.onrender.com",  # Backend domain for docs
        # Add more domains as needed
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Include API routes
app.include_router(properties.router, prefix="/api/v1/properties", tags=["properties"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])

# Include test endpoints
app.include_router(test_endpoints.router, tags=["test"])
app.include_router(hybrid_test_endpoints.router, tags=["hybrid_test"])

# Include explanation endpoints - Phase 3: AI Explanation Generation
app.include_router(explanation_endpoints.router, tags=["explanations"])

# Include security monitoring endpoints - Phase 4: Security & Monitoring
app.include_router(security_endpoints.router, tags=["security"])

# Health check endpoint (with basic rate limiting)
@app.get("/")
@rate_limit_general
async def root(request: Request):
    return {
        "message": "PropMatch API is running!",
        "version": "1.0.0",
        "docs": "/docs",
        "security": "enabled",
        "features": [
            "AI-powered property search",
            "Real-time explanations",
            "Advanced security protection",
            "Rate limiting & DDoS protection",
            "Attack monitoring & analytics"
        ]
    }

@app.get("/health")
async def health_check():
    langsmith_status = get_langsmith_status()
    
    return {
        "status": "healthy", 
        "security": "active",
        "langsmith_tracing": langsmith_status,
        "protection": {
            "rate_limiting": True,
            "ddos_protection": True,
            "prompt_injection_detection": True,
            "ip_blocking": True,
            "attack_monitoring": True
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    ) 