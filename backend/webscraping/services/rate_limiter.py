"""
Rate Limiter
Token bucket algorithm with Redis backend
"""
import time
import logging
from typing import Optional
from django.core.cache import cache

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter
    Supports per-minute and per-hour limits
    """
    
    def __init__(self, config):
        """
        Args:
            config: ScraperConfig instance
        """
        self.config = config
        self.scraper_id = config.id
        
        # Safely get rate limits, fallback to calculating from delay_between_requests
        delay = getattr(config, 'delay_between_requests', 2.0)
        default_per_minute = int(60 / max(delay, 0.1))
        
        self.per_minute_limit = getattr(config, 'rate_limit_per_minute', default_per_minute)
        self.per_hour_limit = getattr(config, 'rate_limit_per_hour', default_per_minute * 60)
    
    def can_proceed(self) -> bool:
        """
        Check if request can proceed based on rate limits
        
        Returns:
            True if within limits, False otherwise
        """
        # Check per-minute limit
        if not self._check_limit('minute', self.per_minute_limit, 60):
            logger.warning(f"Per-minute rate limit exceeded for {self.config.name}")
            return False
        
        # Check per-hour limit
        if not self._check_limit('hour', self.per_hour_limit, 3600):
            logger.warning(f"Per-hour rate limit exceeded for {self.config.name}")
            return False
        
        return True
    
    def _check_limit(self, window: str, limit: int, window_seconds: int) -> bool:
        """
        Check rate limit for specific time window
        
        Args:
            window: 'minute' or 'hour'
            limit: Maximum requests allowed
            window_seconds: Window size in seconds
            
        Returns:
            True if within limit
        """
        cache_key = f"rate_limit:{self.scraper_id}:{window}"
        
        # Get current count
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit:
            return False
        
        # Increment count
        cache.set(cache_key, current_count + 1, window_seconds)
        
        return True
    
    def wait_if_needed(self):
        """
        Wait if rate limit exceeded
        Blocks until rate limit allows
        """
        max_attempts = 10
        attempt = 0
        
        while not self.can_proceed() and attempt < max_attempts:
            wait_time = min(5 * (2 ** attempt), 60)  # Exponential backoff, max 60s
            logger.info(f"Rate limit hit, waiting {wait_time}s...")
            time.sleep(wait_time)
            attempt += 1
        
        if attempt >= max_attempts:
            raise Exception("Rate limit exceeded after maximum wait time")
    
    def reset(self):
        """Reset rate limit counters"""
        cache.delete(f"rate_limit:{self.scraper_id}:minute")
        cache.delete(f"rate_limit:{self.scraper_id}:hour")
        logger.info(f"Rate limits reset for {self.config.name}")
    
    @staticmethod
    def get_remaining(config) -> dict:
        """
        Get remaining requests for scraper
        
        Returns:
            {'per_minute': int, 'per_hour': int}
        """
        scraper_id = config.id
        
        minute_key = f"rate_limit:{scraper_id}:minute"
        hour_key = f"rate_limit:{scraper_id}:hour"
        
        minute_used = cache.get(minute_key, 0)
        hour_used = cache.get(hour_key, 0)
        
        delay = getattr(config, 'delay_between_requests', 2.0)
        default_per_minute = int(60 / max(delay, 0.1))
        per_minute_limit = getattr(config, 'rate_limit_per_minute', default_per_minute)
        per_hour_limit = getattr(config, 'rate_limit_per_hour', default_per_minute * 60)
        
        return {
            'per_minute': max(0, per_minute_limit - minute_used),
            'per_hour': max(0, per_hour_limit - hour_used)
        }


class SimpleRateLimiter:
    """
    Simple in-memory rate limiter (fallback if Redis unavailable)
    """
    
    _requests = {}
    
    def __init__(self, config):
        self.config = config
        self.scraper_id = config.id
        
        delay = getattr(config, 'delay_between_requests', 2.0)
        default_per_minute = int(60 / max(delay, 0.1))
        self.per_minute_limit = getattr(config, 'rate_limit_per_minute', default_per_minute)
    
    def can_proceed(self) -> bool:
        """Check if can proceed (simple implementation)"""
        import time
        
        now = time.time()
        
        if self.scraper_id not in self._requests:
            self._requests[self.scraper_id] = []
        
        # Clean old requests (older than 1 minute)
        self._requests[self.scraper_id] = [
            req_time for req_time in self._requests[self.scraper_id]
            if now - req_time < 60
        ]
        
        # Check limit
        if len(self._requests[self.scraper_id]) >= self.per_minute_limit:
            return False
        
        # Add current request
        self._requests[self.scraper_id].append(now)
        
        return True
