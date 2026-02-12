"""
HuggingFace Serverless Provider - Specialized Models

Features:
- Models: Chronos (time-series), Lag-Llama, and general LLMs
- Speed: Optimized for time-series forecasting
- Use Case: Deep forecasting, trend analysis, specialized domains
- Specialty: Time-series models, domain-specific fine-tuned models
"""

import logging
import os
import requests
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class HuggingFaceProvider:
    """HuggingFace Serverless Provider - Specialized LLM inference"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('HUGGINGFACE_API_KEY', '').strip()
        self.provider_name = "HuggingFace"
        self.available = bool(self.api_key and self.api_key != 'your-hf-api-key-here')
        
        # Default to Chronos for time-series forecasting
        self.model_id = "amazon/chronos-t5-large"
        self.api_url = "https://api-inference.huggingface.co/models"
        
        if self.available:
            logger.info("✅ HuggingFace provider initialized")
        else:
            logger.warning("⚠️ HuggingFace API key not configured")
    
    def is_available(self) -> bool:
        """Check if HuggingFace is configured"""
        return self.available
    
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
        Send request to HuggingFace Serverless API
        
        Args:
            prompt: The prompt to send
            model: Model ID (defaults to chronos-t5-large)
            temperature: Temperature for sampling
            max_tokens: Maximum tokens in response
            
        Returns:
            Tuple of (success: bool, response_text: Optional[str], error: Optional[str])
        """
        if not self.is_available():
            return False, None, "HuggingFace provider not available"
        
        try:
            # Use provided model or default
            model_to_use = model or self.model_id
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare payload - HuggingFace expects inputs field
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": min(max_tokens, 1024),
                    "temperature": temperature,
                    "do_sample": True
                }
            }
            
            # Send request to HuggingFace endpoint
            url = f"{self.api_url}/{model_to_use}"
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ HuggingFace request failed: {error_msg}")
                return False, None, error_msg
            
            # Parse response
            result = response.json()
            
            # Extract text from response - HuggingFace returns list of dicts
            if isinstance(result, list) and len(result) > 0:
                if 'generated_text' in result[0]:
                    response_text = result[0]['generated_text'].strip()
                elif 'summary_text' in result[0]:
                    response_text = result[0]['summary_text'].strip()
                else:
                    response_text = str(result[0]).strip()
            elif isinstance(result, dict) and 'generated_text' in result:
                response_text = result['generated_text'].strip()
            else:
                response_text = str(result).strip()
            
            logger.info(
                f"✅ HuggingFace request successful | Model: {model_to_use} | "
                f"Tokens: {max_tokens}"
            )
            
            return True, response_text, None
            
        except requests.Timeout:
            error_msg = "HuggingFace request timeout"
            logger.error(f"❌ {error_msg}")
            return False, None, error_msg
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ HuggingFace request failed: {error_msg}")
            return False, None, error_msg
    
    def get_model_info(self) -> dict:
        """Get HuggingFace model capabilities"""
        return {
            'name': 'HuggingFace',
            'models': ['chronos-t5-large', 'lag-llama', 'mistral-7b', 'neural-chat-7b'],
            'speed': 'Fast (optimized for time-series)',
            'specialty': 'Time-series forecasting, specialized domains',
            'latency_ms': '100-500',
            'use_case': 'Deep forecasting, domain-specific analysis'
        }
    
    def health_check(self) -> dict:
        """Perform health check on HuggingFace provider"""
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
                    'provider': 'HuggingFace',
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


def get_huggingface_provider() -> HuggingFaceProvider:
    """Factory function to get HuggingFace provider instance"""
    return HuggingFaceProvider()
