"""
Security Monitoring Endpoints
Administrative endpoints for security monitoring and management
"""

from fastapi import APIRouter, HTTPException, status, Request, Depends
from typing import Dict, List, Optional
import logging
from datetime import datetime

from app.core.security import rate_limit_strict, rate_limit_general
from app.core.security_monitor import security_monitor, AttackType, ThreatLevel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/security", tags=["Security Monitoring"])

# Note: In production, these endpoints should be protected with proper authentication
# For now, they use strict rate limiting

@router.get("/health/")
@rate_limit_general
async def security_health(request: Request):
    """
    Security system health check
    
    Security: General rate limiting (100 requests/minute per IP)
    """
    return {
        "status": "healthy",
        "service": "Security Monitoring System",
        "components": {
            "security_monitor": security_monitor is not None and security_monitor.redis_client is not None,
            "rate_limiter": True,
            "attack_detection": True,
            "ip_blocking": True
        }
    }

@router.get("/stats/")
@rate_limit_strict
async def get_security_statistics(request: Request):
    """
    Get comprehensive security statistics
    
    Security: Strict rate limiting (3 requests/minute per IP)
    WARNING: This endpoint exposes sensitive security information
    """
    try:
        if not security_monitor:
            return {
                "error": "Security monitor not available",
                "security_statistics": {},
                "timestamp": None
            }
            
        stats = security_monitor.get_security_stats()
        return {
            "security_statistics": stats,
            "timestamp": security_monitor.redis_client.time()[0] if security_monitor.redis_client else None
        }
    except Exception as e:
        logger.error(f"Error getting security stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security statistics"
        )

@router.get("/events/recent/")
@rate_limit_strict
async def get_recent_security_events(
    request: Request,
    limit: int = 50
):
    """
    Get recent security events
    
    Security: Strict rate limiting (3 requests/minute per IP)
    WARNING: This endpoint exposes sensitive security information
    """
    try:
        # Limit the number of events to prevent abuse
        if limit > 100:
            limit = 100
            
        if not security_monitor:
            return {
                "recent_events": [],
                "count": 0,
                "limit": limit,
                "error": "Security monitor not available"
            }
            
        events = security_monitor.get_recent_events(limit)
        return {
            "recent_events": events,
            "count": len(events),
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error getting recent events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent events"
        )

@router.get("/blocked-ips/")
@rate_limit_strict
async def get_blocked_ips(request: Request):
    """
    Get list of blocked IP addresses
    
    Security: Strict rate limiting (3 requests/minute per IP)
    WARNING: This endpoint exposes sensitive security information
    """
    try:
        if not security_monitor:
            return {
                "blocked_ips": [],
                "count": 0,
                "error": "Security monitor not available"
            }
            
        blocked_ips = security_monitor.get_blocked_ips()
        return {
            "blocked_ips": blocked_ips,
            "count": len(blocked_ips)
        }
    except Exception as e:
        logger.error(f"Error getting blocked IPs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve blocked IPs"
        )

@router.post("/block-ip/")
@rate_limit_strict
async def block_ip_address(
    request: Request,
    ip_address: str,
    reason: str,
    duration_hours: int = 24
):
    """
    Manually block an IP address
    
    Security: Strict rate limiting (3 requests/minute per IP)
    WARNING: This is an administrative function
    """
    try:
        # Validate input
        if not ip_address or not reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="IP address and reason are required"
            )
        
        # Limit duration to reasonable values
        if duration_hours < 1 or duration_hours > 168:  # 1 hour to 1 week
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duration must be between 1 and 168 hours"
            )
        
        # Block the IP
        security_monitor.block_ip(ip_address, f"Manual block: {reason}", duration_hours)
        
        return {
            "message": f"IP {ip_address} blocked successfully",
            "ip_address": ip_address,
            "reason": reason,
            "duration_hours": duration_hours
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error blocking IP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to block IP address"
        )

@router.delete("/unblock-ip/{ip_address}")
@rate_limit_strict
async def unblock_ip_address(request: Request, ip_address: str):
    """
    Manually unblock an IP address
    
    Security: Strict rate limiting (3 requests/minute per IP)
    WARNING: This is an administrative function
    """
    try:
        if not ip_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="IP address is required"
            )
        
        # Unblock the IP
        security_monitor.unblock_ip(ip_address)
        
        return {
            "message": f"IP {ip_address} unblocked successfully",
            "ip_address": ip_address
        }
        
    except Exception as e:
        logger.error(f"Error unblocking IP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unblock IP address"
        )

@router.get("/report/")
@rate_limit_strict
async def generate_security_report(request: Request):
    """
    Generate comprehensive security report
    
    Security: Strict rate limiting (3 requests/minute per IP)
    WARNING: This endpoint exposes detailed security information
    """
    try:
        if not security_monitor:
            return {
                "error": "Security monitor not available",
                "report_generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_events_last_50": 0,
                    "blocked_ips_count": 0,
                    "threat_distribution": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                    "top_attack_types": []
                }
            }
            
        report = security_monitor.generate_security_report()
        return report
    except Exception as e:
        logger.error(f"Error generating security report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate security report"
        )

@router.get("/attack-types/")
@rate_limit_general
async def get_attack_types(request: Request):
    """
    Get list of monitored attack types and threat levels
    
    Security: General rate limiting (100 requests/minute per IP)
    """
    return {
        "attack_types": [attack_type.value for attack_type in AttackType],
        "threat_levels": [threat_level.value for threat_level in ThreatLevel],
        "description": {
            "attack_types": {
                "rate_limit_exceeded": "Too many requests from single IP",
                "ddos_attempt": "Distributed denial of service attack pattern",
                "prompt_injection": "Attempt to inject malicious prompts into AI",
                "sql_injection": "SQL injection attack attempt",
                "suspicious_user_agent": "Bot or automated tool detected",
                "large_payload": "Unusually large request payload",
                "blocked_ip_access": "Access attempt from blocked IP"
            },
            "threat_levels": {
                "low": "Minor security concern, logged for monitoring",
                "medium": "Moderate threat, may trigger rate limiting",
                "high": "Serious threat, may result in IP blocking",
                "critical": "Severe threat, immediate IP blocking"
            }
        }
    }

@router.delete("/events/clear/")
@rate_limit_strict
async def clear_security_events(request: Request):
    """
    Clear all stored security events (maintenance function)
    
    Security: Strict rate limiting (3 requests/minute per IP)
    WARNING: This will delete all security event history
    """
    try:
        if security_monitor.redis_client:
            deleted_count = security_monitor.redis_client.delete(security_monitor.events_key)
            return {
                "message": "Security events cleared successfully",
                "deleted_events": deleted_count
            }
        else:
            return {
                "message": "No events to clear (Redis not available)",
                "deleted_events": 0
            }
    except Exception as e:
        logger.error(f"Error clearing security events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear security events"
        ) 