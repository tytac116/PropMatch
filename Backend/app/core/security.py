"""
Security middleware and utilities for PropMatch API
Includes rate limiting, DDoS protection, bot detection, and prompt injection prevention
"""

import re
import time
import hashlib
import os
from typing import Dict, List, Optional, Set
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
import logging
from datetime import datetime, timedelta

# Import security monitoring
from app.core.security_monitor import (
    security_monitor, 
    log_attack, 
    AttackType, 
    ThreatLevel
)

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduced from INFO to WARNING
logger = logging.getLogger(__name__)

# Redis connection for rate limiting and caching - use environment variables
try:
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        # Use Redis URL from environment - most cloud Redis providers only support db 0
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        logger.info(f"Redis connected for security using URL: {redis_url[:30]}...")
    else:
        # Fallback to localhost if no URL provided
        redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
        redis_client.ping()
        logger.info("Redis connected to localhost")
except Exception as e:
    logger.info(f"Redis not available ({e}), using memory storage for security features")
    redis_client = None

# Rate limiter - use Redis URL or memory storage if Redis is not available
if redis_client and os.getenv('REDIS_URL'):
    # Use the Redis URL directly (cloud providers typically only support db 0)
    limiter = Limiter(key_func=get_remote_address, storage_uri=os.getenv('REDIS_URL'))
elif redis_client:
    limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379/1")
else:
    # Fallback to memory storage when Redis is not available
    limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
    logger.info("Using memory storage for rate limiting")

class SecurityConfig:
    """Security configuration constants"""
    
    # Rate limiting - Updated to 5 requests per minute per IP
    SEARCH_RATE_LIMIT = "5/minute"  # AI search endpoints
    EXPLANATION_RATE_LIMIT = "5/minute"  # AI explanation endpoints
    GENERAL_RATE_LIMIT = "5/minute"  # General endpoints
    STRICT_RATE_LIMIT = "3/minute"  # Most sensitive endpoints
    
    # DDoS protection
    MAX_REQUESTS_PER_IP_PER_HOUR = 500
    MAX_REQUESTS_PER_IP_PER_DAY = 2000
    SUSPICIOUS_THRESHOLD = 50  # requests per minute
    
    # Bot detection
    SUSPICIOUS_USER_AGENTS = [
        'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 'python-requests',
        'postman', 'insomnia', 'httpie', 'automated', 'test'
    ]
    
    # Prompt injection patterns
    PROMPT_INJECTION_PATTERNS = [
        r'ignore\s+previous\s+instructions',
        r'forget\s+everything',
        r'system\s*:',
        r'assistant\s*:',
        r'human\s*:',
        r'<\s*script\s*>',
        r'javascript\s*:',
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__',
        r'subprocess',
        r'os\.system',
        r'shell\s+command',
        r'run\s+command',
        r'execute\s+code',
        r'bypass\s+filter',
        r'jailbreak',
        r'prompt\s+injection',
        r'role\s*:\s*system',
        r'you\s+are\s+now',
        r'pretend\s+to\s+be',
        r'act\s+as\s+if',
        r'simulate\s+being',
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'union\s+select',
        r'drop\s+table',
        r'delete\s+from',
        r'insert\s+into',
        r'update\s+set',
        r'alter\s+table',
        r'create\s+table',
        r'exec\s*\(',
        r'xp_cmdshell',
        r'sp_executesql',
        r'--\s*$',
        r'/\*.*\*/',
        r';\s*--',
        r';\s*#',
    ]

class SecurityMiddleware:
    """Advanced security middleware for API protection"""
    
    def __init__(self):
        self.blocked_ips: Set[str] = set()
        self.suspicious_ips: Dict[str, List[float]] = {}
        self.request_counts: Dict[str, Dict[str, int]] = {}
        
    def is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent indicates bot/automated behavior"""
        if not user_agent:
            return True
            
        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in SecurityConfig.SUSPICIOUS_USER_AGENTS)
    
    def detect_prompt_injection(self, text: str) -> bool:
        """Detect potential prompt injection attempts"""
        if not text:
            return False
            
        text_lower = text.lower()
        
        # Check for prompt injection patterns
        for pattern in SecurityConfig.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning(f"Prompt injection detected: {pattern}")
                return True
                
        # Check for SQL injection patterns
        for pattern in SecurityConfig.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning(f"SQL injection detected: {pattern}")
                return True
                
        return False
    
    def is_ddos_attack(self, ip: str) -> bool:
        """Detect potential DDoS attacks"""
        current_time = time.time()
        
        # Initialize tracking for new IPs
        if ip not in self.suspicious_ips:
            self.suspicious_ips[ip] = []
            
        # Add current request timestamp
        self.suspicious_ips[ip].append(current_time)
        
        # Remove old timestamps (older than 1 minute)
        self.suspicious_ips[ip] = [
            timestamp for timestamp in self.suspicious_ips[ip]
            if current_time - timestamp < 60
        ]
        
        # Check if requests exceed suspicious threshold
        if len(self.suspicious_ips[ip]) > SecurityConfig.SUSPICIOUS_THRESHOLD:
            logger.warning(f"Suspicious activity detected from IP: {ip}")
            return True
            
        return False
    
    def track_request_counts(self, ip: str) -> bool:
        """Track and limit requests per IP"""
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")
        current_day = datetime.now().strftime("%Y-%m-%d")
        
        if ip not in self.request_counts:
            self.request_counts[ip] = {}
            
        # Track hourly requests
        hourly_key = f"hour_{current_hour}"
        daily_key = f"day_{current_day}"
        
        self.request_counts[ip][hourly_key] = self.request_counts[ip].get(hourly_key, 0) + 1
        self.request_counts[ip][daily_key] = self.request_counts[ip].get(daily_key, 0) + 1
        
        # Check limits
        if self.request_counts[ip][hourly_key] > SecurityConfig.MAX_REQUESTS_PER_IP_PER_HOUR:
            logger.warning(f"Hourly limit exceeded for IP: {ip}")
            return False
            
        if self.request_counts[ip][daily_key] > SecurityConfig.MAX_REQUESTS_PER_IP_PER_DAY:
            logger.warning(f"Daily limit exceeded for IP: {ip}")
            return False
            
        return True
    
    def validate_request_size(self, request: Request) -> bool:
        """Validate request size to prevent large payload attacks"""
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > 1024 * 1024:  # 1MB limit
                    logger.warning(f"Large request detected: {size} bytes")
                    return False
            except ValueError:
                return False
        return True
    
    async def security_check(self, request: Request) -> Optional[JSONResponse]:
        """Comprehensive security check for incoming requests"""
        client_ip = get_remote_address(request)
        user_agent = request.headers.get("user-agent", "")
        endpoint = request.url.path
        
        # Check if IP is in security monitor's blocked list
        if security_monitor.is_ip_blocked(client_ip):
            log_attack(
                ip=client_ip,
                attack_type=AttackType.BLOCKED_IP_ACCESS,
                threat_level=ThreatLevel.HIGH,
                endpoint=endpoint,
                user_agent=user_agent
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if IP is in local blocked list
        if client_ip in self.blocked_ips:
            log_attack(
                ip=client_ip,
                attack_type=AttackType.BLOCKED_IP_ACCESS,
                threat_level=ThreatLevel.HIGH,
                endpoint=endpoint,
                user_agent=user_agent
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check request size
        if not self.validate_request_size(request):
            log_attack(
                ip=client_ip,
                attack_type=AttackType.LARGE_PAYLOAD,
                threat_level=ThreatLevel.MEDIUM,
                endpoint=endpoint,
                user_agent=user_agent,
                payload_size=int(request.headers.get("content-length", 0))
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request too large"
            )
        
        # Check for DDoS patterns
        if self.is_ddos_attack(client_ip):
            self.blocked_ips.add(client_ip)
            security_monitor.block_ip(client_ip, "DDoS attack detected", 24)
            log_attack(
                ip=client_ip,
                attack_type=AttackType.DDOS_ATTEMPT,
                threat_level=ThreatLevel.CRITICAL,
                endpoint=endpoint,
                user_agent=user_agent
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests - IP temporarily blocked"
            )
        
        # Check request count limits
        if not self.track_request_counts(client_ip):
            log_attack(
                ip=client_ip,
                attack_type=AttackType.RATE_LIMIT_EXCEEDED,
                threat_level=ThreatLevel.MEDIUM,
                endpoint=endpoint,
                user_agent=user_agent
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Check for suspicious user agents (log but don't block)
        if self.is_suspicious_user_agent(user_agent):
            log_attack(
                ip=client_ip,
                attack_type=AttackType.SUSPICIOUS_USER_AGENT,
                threat_level=ThreatLevel.LOW,
                endpoint=endpoint,
                user_agent=user_agent
            )
        
        return None

# Global security middleware instance
security_middleware = SecurityMiddleware()

def validate_search_input(query: str) -> str:
    """Validate and sanitize search input"""
    if not query or not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty"
        )
    
    # Check for prompt injection
    if security_middleware.detect_prompt_injection(query):
        # Log the attack attempt
        # Note: We can't get request context here, so we'll log with placeholder IP
        logger.warning(f"Prompt injection attempt blocked: {query[:100]}...")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid search query detected"
        )
    
    # Sanitize input
    sanitized = query.strip()
    
    # Limit query length
    if len(sanitized) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query too long (max 500 characters)"
        )
    
    return sanitized

def get_rate_limit_key(request: Request, endpoint: str) -> str:
    """Generate rate limit key based on IP and endpoint"""
    client_ip = get_remote_address(request)
    return f"rate_limit:{endpoint}:{client_ip}"

# Rate limit decorators for different endpoint types
def rate_limit_search(func):
    """Rate limit decorator for AI search endpoints"""
    return limiter.limit(SecurityConfig.SEARCH_RATE_LIMIT)(func)

def rate_limit_explanation(func):
    """Rate limit decorator for AI explanation endpoints"""
    return limiter.limit(SecurityConfig.EXPLANATION_RATE_LIMIT)(func)

def rate_limit_general(func):
    """Rate limit decorator for general endpoints"""
    return limiter.limit(SecurityConfig.GENERAL_RATE_LIMIT)(func)

def rate_limit_strict(func):
    """Rate limit decorator for most sensitive endpoints"""
    return limiter.limit(SecurityConfig.STRICT_RATE_LIMIT)(func)

# Enhanced rate limit exceeded handler with monitoring
def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded with security monitoring"""
    client_ip = get_remote_address(request)
    user_agent = request.headers.get("user-agent", "")
    endpoint = request.url.path
    
    # Get retry_after safely
    retry_after = getattr(exc, 'retry_after', 60)  # Default to 60 seconds if not available
    
    # Log the rate limit violation
    log_attack(
        ip=client_ip,
        attack_type=AttackType.RATE_LIMIT_EXCEEDED,
        threat_level=ThreatLevel.MEDIUM,
        endpoint=endpoint,
        user_agent=user_agent,
        additional_data={"retry_after": retry_after}
    )
    
    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "detail": "Too many requests. Please try again later.",
            "retry_after": retry_after
        }
    )
    response.headers["Retry-After"] = str(retry_after)
    return response 