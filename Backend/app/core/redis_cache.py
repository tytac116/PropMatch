"""
Redis Cache Service for AI Explanations
Integrates with LangChain for intelligent caching of property explanations
"""

import logging
import redis
import hashlib
import json
from typing import Optional, Dict, Any
from langchain_community.cache import RedisCache
from langchain.globals import set_llm_cache

from app.core.config import settings

logger = logging.getLogger(__name__)

class PropertyExplanationCache:
    """Redis-based cache service for AI property explanations"""
    
    def __init__(self):
        self.redis_client = None
        self.langchain_cache = None
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_prefix = "propmatch:explanation:"
        self.ttl_seconds = 86400 * 7  # 7 days cache TTL
        
        self._initialize_redis()
        
    def _fix_redis_url(self, url: str) -> str:
        """Fix Redis URL to ensure proper scheme"""
        if not url:
            return "redis://localhost:6379/0"
        
        # If URL doesn't start with a scheme, add redis://
        if not url.startswith(('redis://', 'rediss://', 'unix://')):
            # If it looks like it has auth info, use rediss:// for security
            if '@' in url:
                return f"rediss://{url}"
            else:
                return f"redis://{url}"
        
        return url
        
    def _initialize_redis(self):
        """Initialize Redis connection and LangChain cache"""
        try:
            if not settings.REDIS_URL:
                logger.warning("Redis URL not configured - caching disabled")
                return
            
            # Fix the Redis URL format
            fixed_redis_url = self._fix_redis_url(settings.REDIS_URL)
            logger.info(f"Attempting Redis connection to: {fixed_redis_url.split('@')[0]}@***" if '@' in fixed_redis_url else fixed_redis_url)
            
            # Initialize Redis client
            self.redis_client = redis.from_url(
                fixed_redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connected successfully!")
            
            # Initialize LangChain Redis cache
            self.langchain_cache = RedisCache(
                redis_=redis.from_url(fixed_redis_url, decode_responses=False)  # LangChain needs binary mode
            )
            set_llm_cache(self.langchain_cache)
            logger.info("LangChain Redis cache initialized")
            
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}")
            logger.info("Explanation service will run without caching")
            self.redis_client = None
            self.langchain_cache = None
    
    def _generate_cache_key(self, search_query: str, listing_number: str) -> str:
        """Generate unique cache key for query + property combination"""
        
        # Create deterministic hash from query + listing_number
        combined_string = f"{search_query.strip().lower()}:{listing_number}"
        cache_hash = hashlib.md5(combined_string.encode()).hexdigest()
        
        return f"{self.cache_prefix}{cache_hash}"
    
    async def get_explanation(self, search_query: str, listing_number: str) -> Optional[Dict[str, Any]]:
        """Get cached explanation for query + property combination"""
        
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(search_query, listing_number)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                self.cache_hits += 1
                logger.info(f"Cache HIT for property {listing_number} (query: {search_query[:50]}...)")
                return json.loads(cached_data)
            else:
                self.cache_misses += 1
                logger.info(f"Cache MISS for property {listing_number} (query: {search_query[:50]}...)")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None
    
    async def set_explanation(self, search_query: str, listing_number: str, explanation: Dict[str, Any]) -> bool:
        """Cache explanation for query + property combination"""
        
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(search_query, listing_number)
            
            # Add metadata
            cache_data = {
                "explanation": explanation,
                "search_query": search_query,
                "listing_number": listing_number,
                "cached_at": json.dumps(None),  # Will be handled by Redis
                "cache_key": cache_key
            }
            
            # Store with TTL
            success = self.redis_client.setex(
                cache_key,
                self.ttl_seconds,
                json.dumps(cache_data)
            )
            
            if success:
                logger.info(f"Cached explanation for property {listing_number} (TTL: {self.ttl_seconds}s)")
                return True
            else:
                logger.warning(f"Failed to cache explanation for property {listing_number}")
                return False
                
        except Exception as e:
            logger.error(f"Error caching explanation: {e}")
            return False
    
    async def invalidate_property_explanations(self, listing_number: str) -> int:
        """Invalidate all cached explanations for a specific property"""
        
        if not self.redis_client:
            return 0
        
        try:
            # Find all keys containing this listing number
            pattern = f"{self.cache_prefix}*"
            keys = self.redis_client.keys(pattern)
            
            deleted_count = 0
            for key in keys:
                try:
                    cached_data = self.redis_client.get(key)
                    if cached_data:
                        data = json.loads(cached_data)
                        if data.get("listing_number") == listing_number:
                            self.redis_client.delete(key)
                            deleted_count += 1
                except:
                    continue
            
            logger.info(f"Invalidated {deleted_count} cached explanations for property {listing_number}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error invalidating cache for property {listing_number}: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_requests": total_requests,
            "hit_rate_percentage": round(hit_rate, 2),
            "redis_connected": self.redis_client is not None,
            "langchain_cache_enabled": self.langchain_cache is not None
        }
        
        # Get Redis info if available
        if self.redis_client:
            try:
                redis_info = self.redis_client.info()
                stats["redis_info"] = {
                    "used_memory_human": redis_info.get("used_memory_human"),
                    "connected_clients": redis_info.get("connected_clients"),
                    "total_commands_processed": redis_info.get("total_commands_processed")
                }
            except:
                stats["redis_info"] = "unavailable"
        
        return stats
    
    async def clear_all_explanations(self) -> int:
        """Clear all explanation cache entries (for maintenance)"""
        
        if not self.redis_client:
            return 0
        
        try:
            pattern = f"{self.cache_prefix}*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted_count} explanation cache entries")
                return deleted_count
            else:
                logger.info("No explanation cache entries to clear")
                return 0
                
        except Exception as e:
            logger.error(f"Error clearing explanation cache: {e}")
            return 0

# Global instance
explanation_cache = PropertyExplanationCache() 