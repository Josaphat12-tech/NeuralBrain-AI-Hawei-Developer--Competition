"""
Security Module - Input Sanitization, Rate Limiting, Secure Headers
Developed by: Bitingo Josaphat JB
"""

import logging
import re
from typing import Dict, Any, Optional
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Sanitizes user input to prevent injection attacks"""
    
    # Patterns for validation
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    ALPHANUMERIC_PATTERN = r'^[a-zA-Z0-9_-]+$'
    NUMERIC_PATTERN = r'^-?\d+\.?\d*$'
    
    # Dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"('\s*OR\s*'|'=')",
        r"(--|\#|\/\*)",
        r"(;|xp_|sp_)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onload\s*=",
    ]
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 255) -> str:
        """
        Sanitize string input.
        
        Args:
            input_str: Input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not isinstance(input_str, str):
            return ""
        
        # Trim to max length
        sanitized = input_str[:max_length].strip()
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Check for dangerous patterns
        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS + InputSanitizer.XSS_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                logger.warning(f"Dangerous pattern detected in input: {pattern}")
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        return bool(re.match(InputSanitizer.EMAIL_PATTERN, email))
    
    @staticmethod
    def validate_numeric(value: Any) -> bool:
        """Validate numeric value"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def sanitize_json_input(data: Dict) -> Dict:
        """
        Recursively sanitize dictionary input.
        
        Args:
            data: Input dictionary
            
        Returns:
            Sanitized dictionary
        """
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            safe_key = InputSanitizer.sanitize_string(str(key), max_length=50)
            
            if isinstance(value, str):
                sanitized[safe_key] = InputSanitizer.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[safe_key] = InputSanitizer.sanitize_json_input(value)
            elif isinstance(value, (int, float, bool)):
                sanitized[safe_key] = value
            elif isinstance(value, list):
                sanitized[safe_key] = [
                    InputSanitizer.sanitize_json_input(item) if isinstance(item, dict) 
                    else InputSanitizer.sanitize_string(str(item)) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                sanitized[safe_key] = str(value)
        
        return sanitized


class RateLimiter:
    """Simple local rate limiter"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Max requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed for identifier.
        
        Args:
            identifier: IP address, user ID, or other identifier
            
        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        return max(0, self.max_requests - len(self.requests[identifier]))


class SecurityHeaders:
    """Secure HTTP headers configuration"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """
        Get recommended security headers.
        
        Returns:
            Dictionary of security headers
        """
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com bootstrap.bundle.min.css",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        }


class SecurityValidator:
    """Validates data for security issues"""
    
    @staticmethod
    def is_safe_parameter(value: Any, param_type: str = 'string') -> bool:
        """
        Validate parameter safety.
        
        Args:
            value: Parameter value
            param_type: 'string', 'email', 'numeric', 'json'
            
        Returns:
            True if safe, False otherwise
        """
        if param_type == 'email':
            return InputSanitizer.validate_email(str(value))
        elif param_type == 'numeric':
            return InputSanitizer.validate_numeric(value)
        elif param_type == 'string':
            sanitized = InputSanitizer.sanitize_string(str(value))
            return len(sanitized) > 0
        elif param_type == 'json':
            try:
                import json
                if isinstance(value, str):
                    json.loads(value)
                return True
            except:
                return False
        
        return False


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(max_requests: int = 100, window_seconds: int = 60) -> RateLimiter:
    """Get or create global rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(max_requests, window_seconds)
    return _rate_limiter


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    Decorator for rate limiting Flask routes.
    
    Args:
        max_requests: Max requests per window
        window_seconds: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request
            limiter = get_rate_limiter(max_requests, window_seconds)
            
            # Use client IP as identifier
            client_ip = request.remote_addr
            
            if not limiter.is_allowed(client_ip):
                return {
                    'error': 'Rate limit exceeded',
                    'remaining': 0
                }, 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
