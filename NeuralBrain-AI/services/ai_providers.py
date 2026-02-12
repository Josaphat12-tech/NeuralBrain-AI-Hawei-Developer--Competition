"""
AI Provider Abstraction Layer

Unified interface for multiple AI providers with automatic failover.
Supports:
- OpenAI (Primary)
- Google Gemini (Secondary/Fallback)

Architecture:
1. AIProvider - Abstract base class
2. OpenAIProvider - OpenAI API implementation
3. GeminiProvider - Google Gemini API implementation
4. AIProviderOrchestrator - Failover logic controller
"""

import logging
import json
import os
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available"""
        pass
    
    @abstractmethod
    def send_request(self, prompt: str, model: str, temperature: float = 0.3, max_tokens: int = 500) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Send request to AI provider
        
        Args:
            prompt: The prompt to send
            model: Model identifier
            temperature: Temperature parameter
            max_tokens: Max tokens in response
            
        Returns:
            Tuple of (success: bool, response_text: Optional[str], error: Optional[str])
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider name for logging"""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI API Provider (Primary)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY', '').strip()
        self.provider_name = "OpenAI"
        self.available = bool(self.api_key and self.api_key != 'sk-your-api-key-here')
        
        if self.available:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info("✅ OpenAI provider initialized")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI initialization failed: {e}")
                self.available = False
                self.client = None
        else:
            self.client = None
            logger.warning("⚠️ OpenAI API key not configured")
    
    def is_available(self) -> bool:
        """Check if OpenAI is configured"""
        return self.available and self.client is not None
    
    def get_provider_name(self) -> str:
        return self.provider_name
    
    def send_request(self, prompt: str, model: str, temperature: float = 0.3, max_tokens: int = 500) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send request to OpenAI API"""
        if not self.is_available():
            return False, None, "OpenAI provider not available"
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.info(f"✅ OpenAI request successful (tokens: {response.usage.total_tokens})")
            return True, response_text, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ OpenAI request failed: {error_msg}")
            return False, None, error_msg


class GeminiProvider(AIProvider):
    """Google Gemini API Provider (Secondary/Fallback)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY', '').strip()
        self.provider_name = "Gemini"
        self.available = bool(self.api_key and self.api_key != 'your-gemini-api-key-here')
        
        if self.available:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai
                logger.info("✅ Gemini provider initialized")
            except Exception as e:
                logger.warning(f"⚠️ Gemini initialization failed: {e}")
                self.available = False
                self.client = None
        else:
            self.client = None
            logger.warning("⚠️ Gemini API key not configured")
    
    def is_available(self) -> bool:
        """Check if Gemini is configured"""
        return self.available and self.client is not None
    
    def get_provider_name(self) -> str:
        return self.provider_name
    
    def send_request(self, prompt: str, model: str, temperature: float = 0.3, max_tokens: int = 500) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send request to Gemini API"""
        if not self.is_available():
            return False, None, "Gemini provider not available"
        
        try:
            # Use Gemini model (gemini-1.5-pro or gemini-1.5-flash available)
            # Fallback to gemini-1.5-flash if pro is requested but unavailable
            gemini_model_name = "gemini-1.5-flash"
            gemini_model = self.client.GenerativeModel(gemini_model_name)
            
            generation_config = self.client.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
            response = gemini_model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            response_text = response.text.strip()
            logger.info(f"✅ Gemini request successful")
            return True, response_text, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Gemini request failed: {error_msg}")
            return False, None, error_msg


class AIProviderOrchestrator:
    """
    Orchestrates AI requests with automatic failover.
    
    Priority:
    1. Try OpenAI (Primary)
    2. If OpenAI fails → Try Gemini (Secondary)
    3. If both fail → Return error
    """
    
    def __init__(self):
        self.openai_provider = OpenAIProvider()
        self.gemini_provider = GeminiProvider()
        self.last_provider_used = None
        self.last_fallback_triggered = None
        
        logger.info("🎯 AI Provider Orchestrator initialized")
        logger.info(f"   OpenAI available: {self.openai_provider.is_available()}")
        logger.info(f"   Gemini available: {self.gemini_provider.is_available()}")
    
    def send_request(self, prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.3, max_tokens: int = 500) -> Tuple[bool, Optional[str], str]:
        """
        Send request with automatic failover.
        
        Returns:
            Tuple of (success: bool, response_text: Optional[str], provider_name: str)
        """
        
        # Try OpenAI first (PRIMARY)
        logger.info(f"📤 Attempting OpenAI ({model})...")
        success, response, error = self.openai_provider.send_request(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if success and response:
            self.last_provider_used = "OpenAI"
            logger.info(f"✅ Used provider: OpenAI (Primary)")
            return True, response, "OpenAI"
        
        logger.warning(f"⚠️ OpenAI failed: {error}")
        
        # Fallback to Gemini (SECONDARY)
        logger.info(f"📤 Falling back to Gemini...")
        self.last_fallback_triggered = datetime.utcnow().isoformat()
        
        success, response, error = self.gemini_provider.send_request(
            prompt=prompt,
            model="gemini-pro",  # Gemini model
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if success and response:
            self.last_provider_used = "Gemini"
            logger.warning(f"⚠️ FAILOVER TRIGGERED: Using Gemini (Secondary)")
            return True, response, "Gemini"
        
        logger.error(f"❌ Gemini also failed: {error}")
        
        # Both failed
        self.last_provider_used = None
        error_msg = f"All AI providers failed. OpenAI: {error}. Gemini: {error}"
        logger.error(f"🔴 CRITICAL: {error_msg}")
        
        return False, None, "NONE"
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get current provider status"""
        return {
            "openai": {
                "available": self.openai_provider.is_available(),
                "provider": "OpenAI"
            },
            "gemini": {
                "available": self.gemini_provider.is_available(),
                "provider": "Gemini"
            },
            "last_used": self.last_provider_used,
            "last_fallback": self.last_fallback_triggered
        }


# Singleton instance
_orchestrator_instance = None

def get_ai_orchestrator() -> AIProviderOrchestrator:
    """Get singleton orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AIProviderOrchestrator()
    return _orchestrator_instance
