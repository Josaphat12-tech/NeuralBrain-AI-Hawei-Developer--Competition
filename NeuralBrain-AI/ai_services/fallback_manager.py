"""
Fallback manager - Handles graceful degradation when cloud services unavailable

Implements smart retry logic, caching, and fallback to original implementations.
"""

import logging
import time
from typing import Callable, Optional, Any, Dict
from functools import wraps

logger = logging.getLogger(__name__)


class FallbackManager:
    """Manages fallback logic and cloud operation failures"""
    
    def __init__(self):
        """Initialize fallback manager"""
        self.last_success = {}
        self.error_counts = {}
    
    def try_cloud_operation(
        self,
        operation_name: str,
        operation: Callable,
        fallback: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Attempt cloud operation with fallback
        
        Args:
            operation_name: Name of operation for logging
            operation: Cloud operation callable
            fallback: Fallback callable if cloud fails
            *args: Arguments to pass to operation/fallback
            **kwargs: Keyword arguments to pass to operation/fallback
        
        Returns:
            Result from operation or fallback
        """
        try:
            result = operation(*args, **kwargs)
            
            if result is not None:
                self.last_success[operation_name] = time.time()
                self.error_counts[operation_name] = 0
                logger.debug(f"{operation_name}: Cloud operation successful")
                return result
            else:
                logger.warning(f"{operation_name}: Cloud returned None, using fallback")
                return fallback(*args, **kwargs)
        
        except Exception as e:
            logger.warning(f"{operation_name}: Cloud operation failed ({str(e)}), using fallback")
            self.error_counts[operation_name] = self.error_counts.get(operation_name, 0) + 1
            
            try:
                return fallback(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(f"{operation_name}: Fallback also failed: {str(fallback_error)}")
                raise
    
    def should_use_cache(self, operation_name: str, cache_ttl: int = 3600) -> bool:
        """
        Determine if cached result should be used
        
        Args:
            operation_name: Name of operation
            cache_ttl: Cache time-to-live in seconds
        
        Returns:
            True if cache should be used
        """
        if operation_name not in self.last_success:
            return False
        
        age = time.time() - self.last_success[operation_name]
        return age < cache_ttl
    
    def get_error_rate(self, operation_name: str) -> float:
        """Get recent error rate for operation"""
        errors = self.error_counts.get(operation_name, 0)
        return min(1.0, errors / max(1, errors + 1))
    
    def reset(self, operation_name: Optional[str] = None):
        """Reset error tracking"""
        if operation_name:
            self.error_counts[operation_name] = 0
            if operation_name in self.last_success:
                del self.last_success[operation_name]
        else:
            self.last_success.clear()
            self.error_counts.clear()


# Global fallback manager instance
fallback_manager = FallbackManager()


def with_fallback(operation_name: str, fallback_fn: Callable):
    """
    Decorator for functions that should have cloud fallback
    
    Usage:
        @with_fallback("health_metrics", fallback_health_metrics)
        def get_health_metrics(patient_id):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"{operation_name} failed, using fallback: {str(e)}")
                return fallback_fn(*args, **kwargs)
        return wrapper
    return decorator
