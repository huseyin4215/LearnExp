"""
Rate Limiter Service
Token bucket algorithm implementation with Redis backend
"""
import time
import logging
from typing import Optional
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token Bucket Rate Limiter
    
    Supports per-minute and per-hour rate limiting
    Uses Django cache (Redis recommended) for distributed rate limiting
    """
    
    def __init__(self, source_name: str, per_minute: int = 60, per_hour: int = 1000):
        """
        Args:
            source_name: Unique identifier for the API source
            per_minute: Maximum requests per minute
            per_hour: Maximum requests per hour
        """
        self.source_name = source_name
        self.per_minute = per_minute
        self.per_hour = per_hour
        
        self.minute_key = f"rate_limit:minute:{source_name}"
        self.hour_key = f"rate_limit:hour:{source_name}"
    
    def can_make_request(self) -> bool:
        """
        Check if request can be made without exceeding rate limits
        
        Returns:
            True if request is allowed, False otherwise
        """
        # Check minute limit
        minute_count = cache.get(self.minute_key, 0)
        if minute_count >= self.per_minute:
            logger.warning(f"Rate limit exceeded (per minute) for {self.source_name}")
            return False
        
        # Check hour limit
        hour_count = cache.get(self.hour_key, 0)
        if hour_count >= self.per_hour:
            logger.warning(f"Rate limit exceeded (per hour) for {self.source_name}")
            return False
        
        return True
    
    def record_request(self):
        """
        Record a request in the rate limiter
        Call this after making a successful request
        """
        # Increment minute counter
        minute_count = cache.get(self.minute_key, 0)
        cache.set(self.minute_key, minute_count + 1, 60)  # 60 seconds TTL
        
        # Increment hour counter
        hour_count = cache.get(self.hour_key, 0)
        cache.set(self.hour_key, hour_count + 1, 3600)  # 3600 seconds TTL
    
    def wait_if_needed(self, max_wait_seconds: int = 60) -> bool:
        """
        Wait if rate limit is exceeded
        
        Args:
            max_wait_seconds: Maximum time to wait
            
        Returns:
            True if waited and can proceed, False if max wait exceeded
        """
        waited = 0
        while not self.can_make_request() and waited < max_wait_seconds:
            time.sleep(1)
            waited += 1
        
        return waited < max_wait_seconds
    
    def get_remaining_requests(self) -> dict:
        """
        Get remaining requests for current windows
        
        Returns:
            {
                'per_minute': {'limit': int, 'used': int, 'remaining': int},
                'per_hour': {'limit': int, 'used': int, 'remaining': int}
            }
        """
        minute_used = cache.get(self.minute_key, 0)
        hour_used = cache.get(self.hour_key, 0)
        
        return {
            'per_minute': {
                'limit': self.per_minute,
                'used': minute_used,
                'remaining': max(0, self.per_minute - minute_used)
            },
            'per_hour': {
                'limit': self.per_hour,
                'used': hour_used,
                'remaining': max(0, self.per_hour - hour_used)
            }
        }
    
    def reset(self):
        """Reset rate limit counters (for testing/admin purposes)"""
        cache.delete(self.minute_key)
        cache.delete(self.hour_key)
        logger.info(f"Rate limit reset for {self.source_name}")


class SimpleRateLimiter:
    """
    Simple in-memory rate limiter (fallback if Redis not available)
    Note: Not suitable for distributed systems
    """
    
    _counters = {}
    
    def __init__(self, source_name: str, per_minute: int = 60, per_hour: int = 1000):
        self.source_name = source_name
        self.per_minute = per_minute
        self.per_hour = per_hour
        
        if source_name not in self._counters:
            self._counters[source_name] = {
                'minute': {'count': 0, 'reset_at': time.time() + 60},
                'hour': {'count': 0, 'reset_at': time.time() + 3600}
            }
    
    def can_make_request(self) -> bool:
        """Check if request is allowed"""
        now = time.time()
        counters = self._counters[self.source_name]
        
        # Reset minute counter if expired
        if now >= counters['minute']['reset_at']:
            counters['minute'] = {'count': 0, 'reset_at': now + 60}
        
        # Reset hour counter if expired
        if now >= counters['hour']['reset_at']:
            counters['hour'] = {'count': 0, 'reset_at': now + 3600}
        
        # Check limits
        if counters['minute']['count'] >= self.per_minute:
            return False
        if counters['hour']['count'] >= self.per_hour:
            return False
        
        return True
    
    def record_request(self):
        """Record a request"""
        counters = self._counters[self.source_name]
        counters['minute']['count'] += 1
        counters['hour']['count'] += 1
    
    def wait_if_needed(self, max_wait_seconds: int = 60) -> bool:
        """Wait if needed"""
        waited = 0
        while not self.can_make_request() and waited < max_wait_seconds:
            time.sleep(1)
            waited += 1
        return waited < max_wait_seconds


def get_rate_limiter(source_name: str, per_minute: int = 60, per_hour: int = 1000):
    """
    Factory function to get appropriate rate limiter
    Uses Redis-backed limiter if available, falls back to simple in-memory limiter
    """
    try:
        # Test if cache backend is working
        cache.set('rate_limiter_test', 1, 1)
        cache.get('rate_limiter_test')
        return RateLimiter(source_name, per_minute, per_hour)
    except Exception as e:
        logger.warning(f"Redis cache not available, using simple rate limiter: {e}")
        return SimpleRateLimiter(source_name, per_minute, per_hour)
