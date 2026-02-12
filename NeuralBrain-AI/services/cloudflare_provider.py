"""
Cloudflare Workers AI Provider - Edge Deployment

Features:
- Models: LLaMA-2-7B, Mistral-7B, and others
- Speed: Edge-local execution (minimal latency)
- Use Case: Regional forecasting, low-latency requirements
- Specialty: Distributed edge computing, global availability
"""

import logging
import os
import requests
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class CloudflareProvider:
    """Cloudflare Workers AI Provider - Edge-based LLM inference"""
    
    def __init__(self, account_id: Optional[str] = None, api_token: Optional[str] = None):
        self.account_id = account_id or os.getenv('CLOUDFLARE_ACCOUNT_ID', '').strip()
        self.api_token = api_token or os.getenv('CLOUDFLARE_API_TOKEN', '').strip()
        self.provider_name = "Cloudflare"
        self.model = "llama-2-7b"  # Default model
        
        # Validate configuration
        self.available = bool(
            self.account_id and 
            self.api_token and 
            self.account_id != 'your-account-id' and
            self.api_token != 'your-api-token'
        )
        
        if self.available:
            self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run"
            logger.info("✅ Cloudflare provider initialized")
        else:
            logger.warning("⚠️ Cloudflare credentials not configured")
            self.base_url = None
    
    def is_available(self) -> bool:
        """Check if Cloudflare is configured"""
        return self.available and self.base_url is not None
    
    def get_provider_name(self) -> str:
        return self.provider_name
    
    def send_request(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.3,
        max_tokens: int = 500
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Send request to Cloudflare Workers AI API
        
        Args:
            prompt: The prompt to send
            model: Model to use (defaults to llama-2-7b)
            temperature: Temperature for sampling
            max_tokens: Maximum tokens in response
            
        Returns:
            Tuple of (success: bool, response_text: Optional[str], error: Optional[str])
        """
        if not self.is_available():
            return False, None, "Cloudflare provider not available"
        
        try:
            # Use provided model or default
            model_to_use = model or self.model
            
            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": prompt,
                "max_tokens": min(max_tokens, 2048),  # Cloudflare limit
                "temperature": temperature
            }
            
            # Send request to Cloudflare endpoint
            url = f"{self.base_url}/{model_to_use}"
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ Cloudflare request failed: {error_msg}")
                return False, None, error_msg
            
            # Parse response
            result = response.json()
            
            # Extract text from response
            if 'result' in result and 'response' in result['result']:
                response_text = result['result']['response'].strip()
            elif 'result' in result and isinstance(result['result'], dict) and 'text' in result['result']:
                response_text = result['result']['text'].strip()
            else:
                response_text = str(result).strip()
            
            logger.info(
                f"✅ Cloudflare request successful | Model: {model_to_use} | "
                f"Tokens: {max_tokens}"
            )
            
            return True, response_text, None
            
        except requests.Timeout:
            error_msg = "Cloudflare request timeout"
            logger.error(f"❌ {error_msg}")
            return False, None, error_msg
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Cloudflare request failed: {error_msg}")
            return False, None, error_msg
    
    def get_model_info(self) -> dict:
        """Get Cloudflare model capabilities"""
        return {
            'name': 'Cloudflare',
            'models': ['llama-2-7b', 'mistral-7b', 'codellama-7b'],
            'speed': 'Very Fast (Edge-local)',
            'specialty': 'Regional forecasting, edge deployment',
            'latency_ms': '10-50',
            'use_case': 'Low-latency inference, global distribution'
        }
    
    def health_check(self) -> dict:
        """Perform health check on Cloudflare provider"""
        try:
            if not self.is_available():
                return {'healthy': False, 'reason': 'Provider not available'}
            
            # Simple health check with minimal tokens
            success, response, error = self.send_request(
                prompt="Reply with just 'ok'",
                temperature=0.0,
                max_tokens=5
            )
            
            if success and response:
                return {
                    'healthy': True,
                    'provider': 'Cloudflare',
                    'status': 'operational'
                }
            else:
                return {
                    'healthy': False,
                    'reason': error or 'Health check failed'
                }
                
        except Exception as e:
            return {
                'healthy': False,
                'reason': str(e)
            }


def get_cloudflare_provider() -> CloudflareProvider:
    """Factory function to get Cloudflare provider instance"""
    return CloudflareProvider()
