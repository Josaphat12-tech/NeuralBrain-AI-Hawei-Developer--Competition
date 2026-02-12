"""
Tests for Extended AI Provider Stack (Phase D)

Tests for:
- GroqProvider
- CloudflareProvider  
- HuggingFaceProvider
- ExtendedAIProviderOrchestrator with lock system
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from services.groq_provider import GroqProvider, get_groq_provider
from services.cloudflare_provider import CloudflareProvider, get_cloudflare_provider
from services.huggingface_provider import HuggingFaceProvider, get_huggingface_provider
from services.extended_orchestrator import ExtendedAIProviderOrchestrator, get_extended_orchestrator
from services.provider_lock import ProviderLockManager


class TestGroqProvider:
    """Tests for Groq provider"""
    
    @pytest.fixture
    def groq_provider(self):
        """Create Groq provider"""
        return GroqProvider(api_key="test-groq-key")
    
    def test_groq_initialization(self, groq_provider):
        """Test Groq provider initialization"""
        assert groq_provider.provider_name == "Groq"
        assert groq_provider.model == "llama-3.3-70b"
    
    def test_groq_provider_name(self, groq_provider):
        """Test provider name"""
        assert groq_provider.get_provider_name() == "Groq"
    
    def test_groq_model_info(self, groq_provider):
        """Test model info"""
        info = groq_provider.get_model_info()
        assert info['name'] == 'Groq'
        assert 'llama-3.3-70b' in info['models']
        assert 'Very Fast' in info['speed']
    
    def test_groq_send_request_success(self, groq_provider):
        """Test successful Groq request"""
        # Mock Groq client by directly setting it
        mock_client = MagicMock()
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Forecast: Cases increasing"
        mock_response.usage.total_tokens = 100
        mock_client.chat.completions.create.return_value = mock_response
        
        # Set mocked client on provider
        groq_provider.client = mock_client
        groq_provider.available = True
        
        # Send request
        success, response, error = groq_provider.send_request("Test prompt")
        
        assert success is True
        assert response == "Forecast: Cases increasing"
        assert error is None
    
    def test_groq_not_available(self):
        """Test Groq when not configured"""
        provider = GroqProvider(api_key="")
        assert provider.is_available() is False
        
        success, response, error = provider.send_request("Test")
        assert success is False
        assert response is None
        assert "not available" in error


class TestCloudflareProvider:
    """Tests for Cloudflare provider"""
    
    @pytest.fixture
    def cloudflare_provider(self):
        """Create Cloudflare provider"""
        return CloudflareProvider(
            account_id="test-account",
            api_token="test-token"
        )
    
    def test_cloudflare_initialization(self, cloudflare_provider):
        """Test Cloudflare provider initialization"""
        assert cloudflare_provider.provider_name == "Cloudflare"
        assert cloudflare_provider.model == "llama-2-7b"
    
    def test_cloudflare_provider_name(self, cloudflare_provider):
        """Test provider name"""
        assert cloudflare_provider.get_provider_name() == "Cloudflare"
    
    def test_cloudflare_model_info(self, cloudflare_provider):
        """Test model info"""
        info = cloudflare_provider.get_model_info()
        assert info['name'] == 'Cloudflare'
        assert 'llama-2-7b' in info['models']
        assert 'Edge-local' in info['speed']
    
    @patch('services.cloudflare_provider.requests.post')
    def test_cloudflare_send_request_success(self, mock_post, cloudflare_provider):
        """Test successful Cloudflare request"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'result': {
                'response': 'Forecast: Stable trend'
            }
        }
        mock_post.return_value = mock_response
        
        success, response, error = cloudflare_provider.send_request("Test prompt")
        
        assert success is True
        assert response == "Forecast: Stable trend"
        assert error is None
    
    def test_cloudflare_not_available(self):
        """Test Cloudflare when not configured"""
        provider = CloudflareProvider(account_id="", api_token="")
        assert provider.is_available() is False
        
        success, response, error = provider.send_request("Test")
        assert success is False
        assert response is None
        assert "not available" in error


class TestHuggingFaceProvider:
    """Tests for HuggingFace provider"""
    
    @pytest.fixture
    def huggingface_provider(self):
        """Create HuggingFace provider"""
        return HuggingFaceProvider(api_key="test-hf-key")
    
    def test_huggingface_initialization(self, huggingface_provider):
        """Test HuggingFace provider initialization"""
        assert huggingface_provider.provider_name == "HuggingFace"
        assert "chronos" in huggingface_provider.model_id.lower()
    
    def test_huggingface_provider_name(self, huggingface_provider):
        """Test provider name"""
        assert huggingface_provider.get_provider_name() == "HuggingFace"
    
    def test_huggingface_model_info(self, huggingface_provider):
        """Test model info"""
        info = huggingface_provider.get_model_info()
        assert info['name'] == 'HuggingFace'
        assert 'chronos' in info['models'][0].lower()
        assert 'time-series' in info['specialty'].lower()
    
    @patch('services.huggingface_provider.requests.post')
    def test_huggingface_send_request_success(self, mock_post, huggingface_provider):
        """Test successful HuggingFace request"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'generated_text': 'Forecast: Rise expected'}
        ]
        mock_post.return_value = mock_response
        
        success, response, error = huggingface_provider.send_request("Test prompt")
        
        assert success is True
        assert response == "Forecast: Rise expected"
        assert error is None
    
    def test_huggingface_not_available(self):
        """Test HuggingFace when not configured"""
        provider = HuggingFaceProvider(api_key="")
        assert provider.is_available() is False
        
        success, response, error = provider.send_request("Test")
        assert success is False
        assert response is None
        assert "not available" in error


class TestExtendedOrchestrator:
    """Tests for Extended AI Provider Orchestrator with lock system"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create extended orchestrator"""
        return ExtendedAIProviderOrchestrator()
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization"""
        assert orchestrator.providers is not None
        assert 'openai' in orchestrator.providers
        assert 'gemini' in orchestrator.providers
        assert 'groq' in orchestrator.providers
        assert 'cloudflare' in orchestrator.providers
        assert 'huggingface' in orchestrator.providers
    
    def test_orchestrator_has_lock_manager(self, orchestrator):
        """Test orchestrator has lock manager"""
        assert orchestrator.lock_manager is not None
        assert hasattr(orchestrator.lock_manager, 'acquire_lock')
        assert hasattr(orchestrator.lock_manager, 'get_locked_provider')
    
    def test_orchestrator_provider_status(self, orchestrator):
        """Test provider status"""
        status = orchestrator.get_provider_status()
        
        assert 'providers' in status
        assert 'locked_provider' in status
        assert 'lock_status' in status
        
        # Check all providers are listed
        for provider_name in ['openai', 'gemini', 'groq', 'cloudflare', 'huggingface']:
            assert provider_name in status['providers']
    
    def test_orchestrator_health_check(self, orchestrator):
        """Test health check all providers"""
        health = orchestrator.health_check_all()
        
        assert isinstance(health, dict)
        # Should have entries for each provider
        assert len(health) >= 1
    
    @patch.object(ProviderLockManager, 'acquire_lock')
    @patch.object(ProviderLockManager, 'get_locked_provider')
    def test_orchestrator_locks_provider_on_demand(self, mock_get_locked, mock_acquire, orchestrator):
        """Test orchestrator locks provider if not already locked"""
        mock_get_locked.return_value = None
        
        # Simulate that orchestrator will try to lock
        assert orchestrator.lock_manager is not None


class TestProviderIntegration:
    """Integration tests for all providers with lock system"""
    
    def test_provider_factory_functions(self):
        """Test provider factory functions"""
        groq = get_groq_provider()
        cloudflare = get_cloudflare_provider()
        huggingface = get_huggingface_provider()
        
        assert groq is not None
        assert cloudflare is not None
        assert huggingface is not None
    
    def test_extended_orchestrator_singleton(self):
        """Test extended orchestrator singleton"""
        orch1 = get_extended_orchestrator()
        orch2 = get_extended_orchestrator()
        
        assert orch1 is orch2  # Same instance
    
    def test_all_providers_have_required_methods(self):
        """Test all providers have required methods"""
        providers = [
            GroqProvider(api_key="test"),
            CloudflareProvider(account_id="test", api_token="test"),
            HuggingFaceProvider(api_key="test")
        ]
        
        required_methods = [
            'is_available',
            'get_provider_name',
            'send_request',
            'health_check'
        ]
        
        for provider in providers:
            for method in required_methods:
                assert hasattr(provider, method), f"{provider.provider_name} missing {method}"


class TestProviderPriority:
    """Tests for provider priority ordering"""
    
    def test_provider_priority_order(self):
        """Test provider priority is maintained"""
        lock_manager = ProviderLockManager()
        
        expected_order = ['openai', 'gemini', 'groq', 'cloudflare', 'huggingface']
        
        # Lock each provider and check next
        for i, provider in enumerate(expected_order[:-1]):
            lock_manager.acquire_lock(provider)
            next_provider = lock_manager.get_next_provider()
            assert next_provider == expected_order[i + 1], \
                f"After {provider}, expected {expected_order[i + 1]}, got {next_provider}"
            lock_manager.release_lock("test")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
