"""
Security Monitoring and Analytics
Tracks attacks, generates alerts, and provides security insights
"""

import logging
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import redis

logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AttackType(Enum):
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    DDOS_ATTEMPT = "ddos_attempt"
    PROMPT_INJECTION = "prompt_injection"
    SQL_INJECTION = "sql_injection"
    SUSPICIOUS_USER_AGENT = "suspicious_user_agent"
    LARGE_PAYLOAD = "large_payload"
    BLOCKED_IP_ACCESS = "blocked_ip_access"

@dataclass
class SecurityEvent:
    """Security event data structure"""
    timestamp: float
    ip_address: str
    attack_type: AttackType
    threat_level: ThreatLevel
    endpoint: str
    user_agent: str
    payload_size: Optional[int] = None
    blocked_content: Optional[str] = None
    additional_data: Optional[Dict] = None

class SecurityMonitor:
    """Security monitoring and alerting system"""
    
    def __init__(self):
        self.redis_client = None
        self.events_key = "security:events"
        self.stats_key = "security:stats"
        self.blocked_ips_key = "security:blocked_ips"
        
        # In-memory fallback storage when Redis is not available
        self.memory_events = []
        self.memory_stats = {}
        self.memory_blocked_ips = set()
        
        try:
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                # Use Redis URL from environment - most cloud Redis providers only support db 0
                # We'll use key prefixes to separate different data types instead of different databases
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info(f"Security monitor connected to Redis: {redis_url[:30]}...")
            else:
                # Fallback to localhost
                self.redis_client = redis.Redis(host='localhost', port=6379, db=2, decode_responses=True)
                self.redis_client.ping()
                logger.info("Security monitor connected to Redis localhost")
        except Exception as e:
            logger.info(f"Security monitor using memory storage ({e})")
            self.redis_client = None
    
    def log_security_event(self, event: SecurityEvent):
        """Log a security event"""
        try:
            # Log important security events only
            if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                logger.warning(
                    f"SECURITY ALERT: {event.attack_type.value} from {event.ip_address} "
                    f"on {event.endpoint} (threat: {event.threat_level.value})"
                )
            
            # Store in Redis if available, otherwise use memory
            if self.redis_client:
                event_data = asdict(event)
                event_data['attack_type'] = event.attack_type.value
                event_data['threat_level'] = event.threat_level.value
                
                # Store event
                self.redis_client.lpush(self.events_key, json.dumps(event_data))
                
                # Keep only last 1000 events
                self.redis_client.ltrim(self.events_key, 0, 999)
                
                # Update statistics
                self._update_stats(event)
            else:
                # Use memory storage
                event_data = asdict(event)
                event_data['attack_type'] = event.attack_type.value
                event_data['threat_level'] = event.threat_level.value
                
                self.memory_events.insert(0, event_data)
                # Keep only last 100 events in memory
                if len(self.memory_events) > 100:
                    self.memory_events = self.memory_events[:100]
                
                # Update memory stats
                self._update_memory_stats(event)
                
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    def _update_stats(self, event: SecurityEvent):
        """Update security statistics"""
        try:
            current_hour = datetime.now().strftime("%Y-%m-%d-%H")
            current_day = datetime.now().strftime("%Y-%m-%d")
            
            # Increment counters
            self.redis_client.hincrby(f"{self.stats_key}:hourly:{current_hour}", event.attack_type.value, 1)
            self.redis_client.hincrby(f"{self.stats_key}:daily:{current_day}", event.attack_type.value, 1)
            self.redis_client.hincrby(f"{self.stats_key}:ip:{event.ip_address}", event.attack_type.value, 1)
            
            # Set expiration
            self.redis_client.expire(f"{self.stats_key}:hourly:{current_hour}", 86400)  # 24 hours
            self.redis_client.expire(f"{self.stats_key}:daily:{current_day}", 604800)  # 7 days
            self.redis_client.expire(f"{self.stats_key}:ip:{event.ip_address}", 86400)  # 24 hours
            
        except Exception as e:
            logger.error(f"Failed to update security stats: {e}")
    
    def _update_memory_stats(self, event: SecurityEvent):
        """Update security statistics in memory"""
        try:
            current_hour = datetime.now().strftime("%Y-%m-%d-%H")
            current_day = datetime.now().strftime("%Y-%m-%d")
            
            # Initialize if not exists
            if current_hour not in self.memory_stats:
                self.memory_stats[current_hour] = {}
            if current_day not in self.memory_stats:
                self.memory_stats[current_day] = {}
            if event.ip_address not in self.memory_stats:
                self.memory_stats[event.ip_address] = {}
            
            # Increment counters
            hourly_key = f"hourly:{current_hour}"
            daily_key = f"daily:{current_day}"
            ip_key = f"ip:{event.ip_address}"
            
            if hourly_key not in self.memory_stats:
                self.memory_stats[hourly_key] = {}
            if daily_key not in self.memory_stats:
                self.memory_stats[daily_key] = {}
            if ip_key not in self.memory_stats:
                self.memory_stats[ip_key] = {}
                
            self.memory_stats[hourly_key][event.attack_type.value] = self.memory_stats[hourly_key].get(event.attack_type.value, 0) + 1
            self.memory_stats[daily_key][event.attack_type.value] = self.memory_stats[daily_key].get(event.attack_type.value, 0) + 1
            self.memory_stats[ip_key][event.attack_type.value] = self.memory_stats[ip_key].get(event.attack_type.value, 0) + 1
            
        except Exception as e:
            logger.error(f"Failed to update memory security stats: {e}")
    
    def get_recent_events(self, limit: int = 100) -> List[Dict]:
        """Get recent security events"""
        try:
            if self.redis_client:
                events = self.redis_client.lrange(self.events_key, 0, limit - 1)
                return [json.loads(event) for event in events]
            else:
                # Use memory storage
                return self.memory_events[:limit]
                
        except Exception as e:
            logger.error(f"Failed to get recent events: {e}")
            return []
    
    def get_security_stats(self) -> Dict:
        """Get comprehensive security statistics"""
        try:
            if self.redis_client:
                current_hour = datetime.now().strftime("%Y-%m-%d-%H")
                current_day = datetime.now().strftime("%Y-%m-%d")
                
                # Get hourly and daily stats
                hourly_stats = self.redis_client.hgetall(f"{self.stats_key}:hourly:{current_hour}")
                daily_stats = self.redis_client.hgetall(f"{self.stats_key}:daily:{current_day}")
                
                # Get top attacking IPs
                ip_keys = self.redis_client.keys(f"{self.stats_key}:ip:*")
                top_ips = []
                
                for ip_key in ip_keys[:10]:  # Limit to top 10
                    ip = ip_key.split(":")[-1]
                    ip_stats = self.redis_client.hgetall(ip_key)
                    total_attacks = sum(int(count) for count in ip_stats.values())
                    top_ips.append({"ip": ip, "total_attacks": total_attacks, "attacks": ip_stats})
                
                # Sort by total attacks
                top_ips.sort(key=lambda x: x["total_attacks"], reverse=True)
                
                return {
                    "current_hour": current_hour,
                    "current_day": current_day,
                    "hourly_stats": hourly_stats,
                    "daily_stats": daily_stats,
                    "top_attacking_ips": top_ips[:5],
                    "total_events_stored": self.redis_client.llen(self.events_key)
                }
            else:
                # Use memory storage
                current_hour = datetime.now().strftime("%Y-%m-%d-%H")
                current_day = datetime.now().strftime("%Y-%m-%d")
                
                hourly_stats = self.memory_stats.get(f"hourly:{current_hour}", {})
                daily_stats = self.memory_stats.get(f"daily:{current_day}", {})
                
                # Get top attacking IPs from memory
                ip_stats = {}
                for key, stats in self.memory_stats.items():
                    if key.startswith("ip:"):
                        ip = key.replace("ip:", "")
                        total_attacks = sum(stats.values())
                        ip_stats[ip] = {"total_attacks": total_attacks, "attacks": stats}
                
                top_ips = sorted(ip_stats.items(), key=lambda x: x[1]["total_attacks"], reverse=True)[:5]
                top_ips = [{"ip": ip, **data} for ip, data in top_ips]
                
                return {
                    "current_hour": current_hour,
                    "current_day": current_day,
                    "hourly_stats": hourly_stats,
                    "daily_stats": daily_stats,
                    "top_attacking_ips": top_ips,
                    "total_events_stored": len(self.memory_events),
                    "storage_type": "memory"
                }
                
        except Exception as e:
            logger.error(f"Failed to get security stats: {e}")
            return {"error": str(e)}
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is in blocked list"""
        try:
            if self.redis_client:
                return self.redis_client.sismember(self.blocked_ips_key, ip)
            else:
                return ip in self.memory_blocked_ips
        except Exception as e:
            logger.error(f"Failed to check blocked IP: {e}")
            return False
    
    def block_ip(self, ip: str, reason: str, duration_hours: int = 24):
        """Block an IP address"""
        try:
            if self.redis_client:
                # Add to blocked set
                self.redis_client.sadd(self.blocked_ips_key, ip)
                
                # Store block reason and expiration
                block_data = {
                    "reason": reason,
                    "blocked_at": datetime.now().isoformat(),
                    "expires_at": (datetime.now() + timedelta(hours=duration_hours)).isoformat()
                }
                self.redis_client.setex(f"security:block_info:{ip}", duration_hours * 3600, json.dumps(block_data))
            else:
                # Use memory storage
                self.memory_blocked_ips.add(ip)
                
            # Log the block
            self.log_security_event(SecurityEvent(
                timestamp=time.time(),
                ip_address=ip,
                attack_type=AttackType.BLOCKED_IP_ACCESS,
                threat_level=ThreatLevel.HIGH,
                endpoint="system",
                user_agent="system",
                additional_data={"reason": reason, "duration_hours": duration_hours}
            ))
            
            logger.warning(f"Blocked IP {ip} for {duration_hours} hours. Reason: {reason}")
                
        except Exception as e:
            logger.error(f"Failed to block IP {ip}: {e}")
    
    def unblock_ip(self, ip: str):
        """Unblock an IP address"""
        try:
            if self.redis_client:
                self.redis_client.srem(self.blocked_ips_key, ip)
                self.redis_client.delete(f"security:block_info:{ip}")
            else:
                self.memory_blocked_ips.discard(ip)
            logger.info(f"Unblocked IP {ip}")
        except Exception as e:
            logger.error(f"Failed to unblock IP {ip}: {e}")
    
    def get_blocked_ips(self) -> List[Dict]:
        """Get list of blocked IPs with details"""
        try:
            if self.redis_client:
                blocked_ips = self.redis_client.smembers(self.blocked_ips_key)
                blocked_list = []
                
                for ip in blocked_ips:
                    block_info_key = f"security:block_info:{ip}"
                    block_info = self.redis_client.get(block_info_key)
                    
                    if block_info:
                        info = json.loads(block_info)
                        blocked_list.append({
                            "ip": ip,
                            "reason": info.get("reason"),
                            "blocked_at": info.get("blocked_at"),
                            "expires_at": info.get("expires_at")
                        })
                    else:
                        # Clean up orphaned entries
                        self.redis_client.srem(self.blocked_ips_key, ip)
                
                return blocked_list
            else:
                # Use memory storage - simplified without expiration tracking
                return [{"ip": ip, "reason": "Memory storage", "blocked_at": datetime.now().isoformat(), "expires_at": "N/A"} 
                       for ip in self.memory_blocked_ips]
            
        except Exception as e:
            logger.error(f"Failed to get blocked IPs: {e}")
            return []
    
    def generate_security_report(self) -> Dict:
        """Generate comprehensive security report"""
        try:
            stats = self.get_security_stats()
            recent_events = self.get_recent_events(50)
            blocked_ips = self.get_blocked_ips()
            
            # Analyze threat levels
            threat_analysis = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
            
            for event in recent_events:
                threat_level = event.get("threat_level", "low")
                threat_analysis[threat_level] = threat_analysis.get(threat_level, 0) + 1
            
            # Calculate attack trends
            attack_types = {}
            for event in recent_events:
                attack_type = event.get("attack_type", "unknown")
                attack_types[attack_type] = attack_types.get(attack_type, 0) + 1
            
            return {
                "report_generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_events_last_50": len(recent_events),
                    "blocked_ips_count": len(blocked_ips),
                    "threat_distribution": threat_analysis,
                    "top_attack_types": sorted(attack_types.items(), key=lambda x: x[1], reverse=True)[:5]
                },
                "statistics": stats,
                "recent_events": recent_events[:10],  # Last 10 events
                "blocked_ips": blocked_ips,
                "recommendations": self._generate_recommendations(stats, recent_events),
                "storage_type": "memory" if not self.redis_client else "redis"
            }
            
        except Exception as e:
            logger.error(f"Failed to generate security report: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self, stats: Dict, recent_events: List[Dict]) -> List[str]:
        """Generate security recommendations based on current data"""
        recommendations = []
        
        try:
            # Check for high attack volumes
            if self.redis_client:
                daily_stats = stats.get("daily_stats", {})
            else:
                daily_stats = stats.get("daily_stats", {})
            
            total_daily_attacks = sum(int(count) for count in daily_stats.values()) if daily_stats else 0
            
            if total_daily_attacks > 100:
                recommendations.append("High attack volume detected. Consider implementing stricter rate limits.")
            
            # Check for prompt injection attempts
            prompt_injections = int(daily_stats.get("prompt_injection", 0)) if daily_stats else 0
            if prompt_injections > 10:
                recommendations.append("Multiple prompt injection attempts detected. Review AI input validation.")
            
            # Check for DDoS patterns
            ddos_attempts = int(daily_stats.get("ddos_attempt", 0)) if daily_stats else 0
            if ddos_attempts > 5:
                recommendations.append("DDoS attempts detected. Consider implementing additional DDoS protection.")
            
            # Check for diverse attack sources
            top_ips = stats.get("top_attacking_ips", [])
            if len(top_ips) > 10:
                recommendations.append("Attacks from multiple IPs detected. Consider geographic blocking if appropriate.")
            
            if not recommendations:
                recommendations.append("Security posture looks good. Continue monitoring.")
                
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("Unable to generate recommendations due to error.")
        
        return recommendations

# Global security monitor instance
try:
    security_monitor = SecurityMonitor()
    logger.info("Security monitor initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize security monitor: {e}")
    # Create a minimal fallback
    security_monitor = None

def log_attack(ip: str, attack_type: AttackType, threat_level: ThreatLevel, 
               endpoint: str, user_agent: str = "", **kwargs):
    """Convenience function to log security attacks"""
    try:
        event = SecurityEvent(
            timestamp=time.time(),
            ip_address=ip,
            attack_type=attack_type,
            threat_level=threat_level,
            endpoint=endpoint,
            user_agent=user_agent,
            **kwargs
        )
        if security_monitor:
            security_monitor.log_security_event(event)
        else:
            # Fallback logging when security monitor is not available
            logger.warning(
                f"SECURITY EVENT (fallback): {attack_type.value} from {ip} "
                f"on {endpoint} (threat: {threat_level.value})"
            )
    except Exception as e:
        logger.error(f"Failed to log security attack: {e}") 