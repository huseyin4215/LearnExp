"""
Retry Handler
Implements retry logic with exponential backoff
"""
import time
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


class RetryHandler:
    """
    Retry handler with exponential backoff
    """
    
    def __init__(self, config):
        """
        Args:
            config: ScraperConfig instance
        """
        self.config = config
        self.max_retries = getattr(config, 'max_retries', 3)
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries - 1:
                    wait_time = self._calculate_backoff(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed for {self.config.name}: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"All {self.max_retries} attempts failed for {self.config.name}: {e}"
                    )
        
        # All retries exhausted
        raise last_exception
    
    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff time
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Wait time in seconds
        """
        # Exponential backoff: 2^attempt seconds, capped at 60s
        base_delay = 2
        max_delay = 60
        
        delay = min(base_delay ** (attempt + 1), max_delay)
        
        return delay
    
    @staticmethod
    def retry_on_exception(max_retries: int = 3, exceptions: tuple = (Exception,)):
        """
        Decorator for retry logic
        
        Usage:
            @RetryHandler.retry_on_exception(max_retries=3)
            def my_function():
                ...
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt < max_retries - 1:
                            wait_time = 2 ** (attempt + 1)
                            logger.warning(f"Retry {attempt + 1}/{max_retries}: {e}")
                            time.sleep(wait_time)
                
                raise last_exception
            
            return wrapper
        return decorator
