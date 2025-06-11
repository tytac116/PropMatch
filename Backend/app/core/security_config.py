"""
Production Security Configuration
Environment-based security settings for deployment
"""

import os
from typing import List, Dict, Any
from pydantic import BaseSettings

class SecuritySettings(BaseSettings):
    """Security configuration settings"""
    
    # Rate Limiting Configuration
    SEARCH_RATE_LIMIT: str = os.getenv("SEARCH_RATE_LIMIT", "10/minute")
    EXPLANATION_RATE_LIMIT: str = os.getenv("EXPLANATION_RATE_LIMIT", "5/minute")
    GENERAL_RATE_LIMIT: str = os.getenv("GENERAL_RATE_LIMIT", "100/minute")
    STRICT_RATE_LIMIT: str = os.getenv("STRICT_RATE_LIMIT", "3/minute")
    
    # DDoS Protection
    MAX_REQUESTS_PER_IP_PER_HOUR: int = int(os.getenv("MAX_REQUESTS_PER_IP_PER_HOUR", "500"))
    MAX_REQUESTS_PER_IP_PER_DAY: int = int(os.getenv("MAX_REQUESTS_PER_IP_PER_DAY", "2000"))
    SUSPICIOUS_THRESHOLD: int = int(os.getenv("SUSPICIOUS_THRESHOLD", "50"))
    
    # Request Size Limits
    MAX_REQUEST_SIZE_MB: int = int(os.getenv("MAX_REQUEST_SIZE_MB", "1"))
    MAX_QUERY_LENGTH: int = int(os.getenv("MAX_QUERY_LENGTH", "500"))
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_RATE_LIMIT_DB: int = int(os.getenv("REDIS_RATE_LIMIT_DB", "1"))
    REDIS_SECURITY_DB: int = int(os.getenv("REDIS_SECURITY_DB", "2"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    
    # Trusted Hosts (for production)
    TRUSTED_HOSTS: List[str] = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1").split(",")
    
    # CORS Origins (for production)
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # Security Features Toggle
    ENABLE_RATE_LIMITING: bool = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
    ENABLE_DDOS_PROTECTION: bool = os.getenv("ENABLE_DDOS_PROTECTION", "true").lower() == "true"
    ENABLE_PROMPT_INJECTION_DETECTION: bool = os.getenv("ENABLE_PROMPT_INJECTION_DETECTION", "true").lower() == "true"
    ENABLE_IP_BLOCKING: bool = os.getenv("ENABLE_IP_BLOCKING", "true").lower() == "true"
    ENABLE_ATTACK_MONITORING: bool = os.getenv("ENABLE_ATTACK_MONITORING", "true").lower() == "true"
    
    # Logging Configuration
    SECURITY_LOG_LEVEL: str = os.getenv("SECURITY_LOG_LEVEL", "INFO")
    ENABLE_SECURITY_ALERTS: bool = os.getenv("ENABLE_SECURITY_ALERTS", "true").lower() == "true"
    
    # IP Blocking Configuration
    DEFAULT_BLOCK_DURATION_HOURS: int = int(os.getenv("DEFAULT_BLOCK_DURATION_HOURS", "24"))
    MAX_BLOCK_DURATION_HOURS: int = int(os.getenv("MAX_BLOCK_DURATION_HOURS", "168"))  # 1 week
    
    # Monitoring Configuration
    SECURITY_EVENTS_RETENTION_HOURS: int = int(os.getenv("SECURITY_EVENTS_RETENTION_HOURS", "168"))  # 1 week
    MAX_STORED_EVENTS: int = int(os.getenv("MAX_STORED_EVENTS", "1000"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global security settings instance
security_settings = SecuritySettings()

def get_redis_url(db: int = 1) -> str:
    """Get Redis URL for rate limiting or security monitoring"""
    if security_settings.REDIS_PASSWORD:
        return f"redis://:{security_settings.REDIS_PASSWORD}@{security_settings.REDIS_HOST}:{security_settings.REDIS_PORT}/{db}"
    else:
        return f"redis://{security_settings.REDIS_HOST}:{security_settings.REDIS_PORT}/{db}"

def get_security_headers() -> Dict[str, str]:
    """Get security headers for HTTP responses"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'",
        "X-Security-Enabled": "true"
    }

def is_production() -> bool:
    """Check if running in production environment"""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"

def get_environment_config() -> Dict[str, Any]:
    """Get environment-specific configuration"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return {
            "debug": False,
            "reload": False,
            "log_level": "warning",
            "access_log": True,
            "security_strict": True,
            "rate_limits_strict": True
        }
    elif env == "staging":
        return {
            "debug": False,
            "reload": False,
            "log_level": "info",
            "access_log": True,
            "security_strict": True,
            "rate_limits_strict": False
        }
    else:  # development
        return {
            "debug": True,
            "reload": True,
            "log_level": "debug",
            "access_log": False,
            "security_strict": False,
            "rate_limits_strict": False
        }

# Production security recommendations
PRODUCTION_SECURITY_CHECKLIST = [
    "Set ENVIRONMENT=production",
    "Configure TRUSTED_HOSTS with your domain",
    "Set CORS_ORIGINS to your frontend domains only",
    "Use strong Redis password (REDIS_PASSWORD)",
    "Enable all security features",
    "Set appropriate rate limits for your traffic",
    "Configure proper logging and monitoring",
    "Use HTTPS in production",
    "Set up proper firewall rules",
    "Monitor security endpoints regularly"
]

def validate_production_config() -> List[str]:
    """Validate production security configuration"""
    warnings = []
    
    if is_production():
        if "localhost" in security_settings.TRUSTED_HOSTS:
            warnings.append("Remove localhost from TRUSTED_HOSTS in production")
        
        if "http://localhost:3000" in security_settings.CORS_ORIGINS:
            warnings.append("Remove localhost from CORS_ORIGINS in production")
        
        if not security_settings.REDIS_PASSWORD:
            warnings.append("Set REDIS_PASSWORD for production Redis instance")
        
        if security_settings.MAX_REQUESTS_PER_IP_PER_HOUR > 1000:
            warnings.append("Consider lowering MAX_REQUESTS_PER_IP_PER_HOUR for production")
        
        if not all([
            security_settings.ENABLE_RATE_LIMITING,
            security_settings.ENABLE_DDOS_PROTECTION,
            security_settings.ENABLE_PROMPT_INJECTION_DETECTION,
            security_settings.ENABLE_IP_BLOCKING,
            security_settings.ENABLE_ATTACK_MONITORING
        ]):
            warnings.append("All security features should be enabled in production")
    
    return warnings 