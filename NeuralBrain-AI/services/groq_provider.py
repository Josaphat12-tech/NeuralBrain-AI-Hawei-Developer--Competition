"""
Groq AI Provider - High-Speed Inference

Features:
- Models: llama-3.3-70b, llama-3.1-8b, mixtral-8x7b
- Speed: 5-10x faster than standard LLMs
- Use Case: Numerical forecasting, trend analysis, real-time inference
- Specialty: Very fast token generation (tokens/sec)
"""

import logging
import os
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import Groq at module level for testing
try:
    from groq import Groq
except ImportError:
    Groq = None


class GroqProvider:
    """Groq API Provider - Ultra-fast LLM inference"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY', '').strip()
        self.provider_name = "Groq"
        self.available = bool(self.api_key and self.api_key != 'your-groq-api-key-here')
        self.model = "llama-3.1-8b-instant"  # Default model (fastest)
        self.client = None
        
        if self.available and Groq is not None:
            try:
                self.client = Groq(api_key=self.api_key)
                logger.info("✅ Groq provider initialized")
            except Exception as e:
                logger.warning(f"⚠️ Groq initialization failed: {e}")
                self.available = False
                self.client = None
        else:
            if self.available:
                logger.warning("⚠️ Groq library not installed")
    
    def is_available(self) -> bool:
        """Check if Groq is configured"""
        return self.available and self.client is not None
    
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
        Send request to Groq API
        
        Args:
            prompt: The prompt to send
            model: Model to use (defaults to llama-3.3-70b)
            temperature: Temperature for sampling
            max_tokens: Maximum tokens in response
            
        Returns:
            Tuple of (success: bool, response_text: Optional[str], error: Optional[str])
        """
        if not self.is_available():
            return False, None, "Groq provider not available"
        
        try:
            # Use provided model or default
            model_to_use = model or self.model
            
            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Log performance metrics
            if hasattr(response, 'usage'):
                logger.info(
                    f"✅ Groq request successful | Model: {model_to_use} | "
                    f"Tokens: {response.usage.total_tokens}"
                )
            else:
                logger.info(f"✅ Groq request successful | Model: {model_to_use}")
            
            return True, response_text, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Groq request failed: {error_msg}")
            return False, None, error_msg
    
    def get_model_info(self) -> dict:
        """Get Groq model capabilities"""
        return {
            'name': 'Groq',
            'models': ['llama-3.3-70b', 'llama-3.1-8b', 'mixtral-8x7b'],
            'speed': 'Very Fast (5-10x standard)',
            'specialty': 'High-speed token generation',
            'latency_ms': '50-200',
            'use_case': 'Numerical forecasting, real-time inference'
        }
    
    def health_check(self) -> dict:
        """Perform health check on Groq provider"""
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
                    'provider': 'Groq',
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


def get_groq_provider() -> GroqProvider:
    """Factory function to get Groq provider instance"""
    return GroqProvider()
