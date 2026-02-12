"""
Base HTTP client for Huawei Cloud APIs

Handles authentication, timeouts, retries, and error handling.
"""

import requests
import logging
import time
from typing import Dict, Any, Optional
from requests.exceptions import RequestException, Timeout, ConnectionError, URLRequired

logger = logging.getLogger(__name__)


class HuaweiAPIClient:
    """Client for making authenticated requests to Huawei Cloud APIs"""
    
    def __init__(self, api_key: str, endpoint: str, timeout: int = 5):
        """
        Initialize Huawei API client
        
        Args:
            api_key: Huawei Cloud API key for authentication
            endpoint: Base API endpoint URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = timeout
        self.session = requests.Session()
        self._setup_headers()
    
    def _setup_headers(self):
        """Configure default headers for all requests"""
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "NeuralBrain-AI/1.0",
        })
        
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "X-Auth-Token": self.api_key,
            })
    
    def post(self, endpoint_path: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Make authenticated POST request to Huawei API
        
        Args:
            endpoint_path: API endpoint path (relative to base endpoint)
            payload: Request payload as dictionary
        
        Returns:
            Response JSON as dictionary, or None on error
        """
        url = f"{self.endpoint}{endpoint_path}"
        
        try:
            self._log_request(endpoint_path, payload)
            
            start_time = time.time()
            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            latency = time.time() - start_time
            
            self._log_response(response, latency)
            response.raise_for_status()
            
            return response.json()
        
        except Timeout:
            logger.warning(f"⏱️ Timeout calling {endpoint_path} (>{self.timeout}s). Using fallback.")
            return None
        
        except (ConnectionError, URLRequired) as e:
            logger.warning(f"🔌 Connection error to {endpoint_path}: Huawei service unreachable. Using fallback.")
            return None
        
        except requests.exceptions.URLRequired as e:
            logger.warning(f"Invalid URL for {endpoint_path}: {str(e)[:80]}. Using fallback.")
            return None
        
        except requests.exceptions.InvalidURL as e:
            logger.warning(f"Invalid URL format for {endpoint_path}: {str(e)[:80]}. Using fallback.")
            return None
        
        except requests.exceptions.HTTPError as e:
            status_code = response.status_code if 'response' in locals() else "unknown"
            logger.error(f"HTTP error {status_code} from {endpoint_path}: {str(e)}")
            
            # Log rate limiting
            if status_code == 429:
                logger.warning("Rate limited by Huawei Cloud API")
            
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error calling {endpoint_path}: {str(e)[:150]}")
            return None
    
    def _log_request(self, endpoint: str, payload: Dict[str, Any]):
        """Log outgoing request for debugging"""
        if logger.isEnabledFor(logging.DEBUG):
            # Mask sensitive data
            safe_payload = {k: v for k, v in payload.items() if k != "api_key"}
            logger.debug(f"API Request: POST {endpoint}")
            logger.debug(f"Payload: {safe_payload}")
    
    def _log_response(self, response: requests.Response, latency: float):
        """Log response for monitoring"""
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"API Response: Status {response.status_code} (latency: {latency:.3f}s)")
        
        if response.status_code >= 400:
            logger.warning(f"Error response {response.status_code}: {response.text[:200]}")
    
    def close(self):
        """Close the session"""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
