"""
Extended AI Provider Orchestrator with Lock System Integration

This module extends the original orchestrator to:
1. Use the new provider lock system for deterministic routing
2. Support 5 AI providers instead of 2
3. Integrate with the bottleneck forecasting engine
4. Provide automatic failover with lock management

Provider Stack (Priority Order):
1. OpenAI (Primary)
2. Gemini (Secondary)
3. Groq (Tertiary)
4. Cloudflare (Quaternary)
5. HuggingFace (Final)
"""

import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ExtendedAIProviderOrchestrator:
    """
    Extended orchestrator with 5 providers and lock system integration
    """
    
    def __init__(self):
        """Initialize all 5 providers"""
        # Import provider lock system
        from services.provider_lock import get_provider_lock_manager
        from services.ai_providers import OpenAIProvider, GeminiProvider
        from services.groq_provider import GroqProvider
        from services.cloudflare_provider import CloudflareProvider
        from services.huggingface_provider import HuggingFaceProvider
        
        # Initialize lock manager
        self.lock_manager = get_provider_lock_manager()
        
        # Initialize all 5 providers
        self.providers = {
            'openai': OpenAIProvider(),
            'gemini': GeminiProvider(),
            'groq': GroqProvider(),
            'cloudflare': CloudflareProvider(),
            'huggingface': HuggingFaceProvider()
        }
        
        # Track which providers are available
        self.available_providers = [
            name for name, provider in self.providers.items()
            if provider.is_available()
        ]
        
        # Log initialization
        logger.info("🎯 Extended AI Provider Orchestrator initialized")
        for provider_name in self.available_providers:
            logger.info(f"   ✅ {provider_name.upper()} available")
        
        unavailable = [name for name in self.providers.keys() if name not in self.available_providers]
        for provider_name in unavailable:
            logger.warning(f"   ⚠️ {provider_name.upper()} not available")
    
    def get_prediction(
        self,
        prompt: str,
        region: str = "Global",
        model: str = None,
        temperature: float = 0.3,
        max_tokens: int = 500
    ) -> Tuple[bool, Optional[str], str]:
        """
        Get prediction from locked provider with automatic failover
        
        Args:
            prompt: Prediction prompt
            region: Geographic region (for logging)
            model: Specific model to use (optional)
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            
        Returns:
            Tuple of (success: bool, response: Optional[str], provider_used: str)
        """
        # Ensure a provider is locked
        locked_provider = self.lock_manager.get_locked_provider()
        
        if not locked_provider:
            # Lock default provider (OpenAI)
            self.lock_manager.acquire_lock('openai')
            locked_provider = 'openai'
            logger.info(f"🔒 Locked provider: {locked_provider} (default)")
        
        logger.info(f"📤 Using locked provider: {locked_provider}")
        
        try:
            # Get locked provider instance
            provider = self.providers[locked_provider]
            
            if not provider.is_available():
                raise Exception(f"Locked provider {locked_provider} is not available")
            
            # Send request
            success, response, error = provider.send_request(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if success and response:
                # Reset failure count on success
                self.lock_manager.reset_failure_count()
                logger.info(f"✅ {locked_provider} succeeded for {region}")
                return True, response, locked_provider
            else:
                # Increment failure count
                failure_count = self.lock_manager.increment_failure_count(1)
                logger.warning(
                    f"⚠️ {locked_provider} failed for {region} "
                    f"(failures: {failure_count})"
                )
                
                # Check if failover threshold reached
                if failure_count >= 3:
                    return self._trigger_failover(prompt, region, model, temperature, max_tokens)
                else:
                    return False, None, locked_provider
        
        except Exception as e:
            logger.error(f"❌ {locked_provider} error: {str(e)}")
            
            # Trigger failover
            failure_count = self.lock_manager.increment_failure_count(1)
            if failure_count >= 3:
                return self._trigger_failover(prompt, region, model, temperature, max_tokens)
            else:
                return False, None, locked_provider
    
    def _trigger_failover(
        self,
        prompt: str,
        region: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Tuple[bool, Optional[str], str]:
        """
        Trigger failover to next provider in priority
        
        Returns:
            Tuple of (success: bool, response: Optional[str], provider_used: str)
        """
        current_provider = self.lock_manager.get_locked_provider()
        logger.warning(f"🔄 Failover triggered from {current_provider}")
        
        # Release current lock
        self.lock_manager.release_lock("failover")
        
        # Get next provider
        next_provider = self.lock_manager.get_next_provider()
        
        if not next_provider:
            logger.error("❌ No providers available for failover!")
            return False, None, "NONE"
        
        # Lock next provider
        self.lock_manager.acquire_lock(next_provider)
        logger.info(f"✅ Switched to {next_provider}")
        
        # Retry with new provider
        try:
            provider = self.providers[next_provider]
            
            success, response, error = provider.send_request(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if success and response:
                self.lock_manager.reset_failure_count()
                logger.info(f"✅ Failover to {next_provider} succeeded for {region}")
                return True, response, next_provider
            else:
                logger.error(f"❌ Failover provider {next_provider} failed: {error}")
                return False, None, next_provider
        
        except Exception as e:
            logger.error(f"❌ Failover provider {next_provider} error: {str(e)}")
            return False, None, next_provider
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get comprehensive provider status"""
        status = {
            'providers': {},
            'locked_provider': self.lock_manager.get_locked_provider(),
            'lock_status': self.lock_manager.get_status()
        }
        
        for provider_name, provider in self.providers.items():
            status['providers'][provider_name] = {
                'available': provider.is_available(),
                'name': provider.get_provider_name(),
                'model_info': provider.get_model_info() if hasattr(provider, 'get_model_info') else None
            }
        
        return status
    
    def health_check_all(self) -> Dict[str, Any]:
        """Check health of all providers"""
        health_status = {}
        
        for provider_name, provider in self.providers.items():
            if not provider.is_available():
                health_status[provider_name] = {
                    'healthy': False,
                    'reason': 'Not configured'
                }
            elif hasattr(provider, 'health_check'):
                health_status[provider_name] = provider.health_check()
            else:
                health_status[provider_name] = {
                    'healthy': provider.is_available(),
                    'status': 'available'
                }
        
        return health_status


# Singleton instance
_extended_orchestrator_instance = None


def get_extended_orchestrator() -> ExtendedAIProviderOrchestrator:
    """Get singleton extended orchestrator instance"""
    global _extended_orchestrator_instance
    if _extended_orchestrator_instance is None:
        _extended_orchestrator_instance = ExtendedAIProviderOrchestrator()
    return _extended_orchestrator_instance
