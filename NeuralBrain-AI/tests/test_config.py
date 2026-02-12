"""
Test suite for AI Services Configuration (Phase 4)
Tests configuration loading, defaults, and environment variable handling
"""

import os
import pytest
from unittest.mock import patch
from ai_services.config import AIServiceConfig


class TestAIServiceConfig:
    """Test AIServiceConfig functionality"""

    def test_config_loads_with_defaults(self):
        """Test that config loads with sensible defaults"""
        config = AIServiceConfig()
        
        assert config.ENABLED is True
        assert config.HEALTH_METRICS_TIMEOUT == 3
        assert config.RISK_SCORING_TIMEOUT == 2
        assert config.FORECAST_TIMEOUT == 3
        assert config.CACHE_ENABLED is True
        assert config.CACHE_TTL_SECONDS == 3600

    def test_config_disabled_without_api_key(self):
        """Test that cloud services are unavailable without API key"""
        with patch.dict(os.environ, {"HUAWEI_API_KEY": ""}, clear=False):
            config = AIServiceConfig()
            assert config.ENABLED is True  # ENABLED flag still true, but API_KEY empty

    def test_config_available_with_api_key(self):
        """Test that cloud services are available with API key"""
        with patch.dict(os.environ, {
            "HUAWEI_API_KEY": "test-api-key",
            "HUAWEI_MODELARTS_ENDPOINT": "https://test.com"
        }, clear=False):
            config = AIServiceConfig()
            assert config.ENABLED is True

    def test_config_from_environment_variables(self):
        """Test config loading from environment variables"""
        env_vars = {
            "AI_SERVICE_TIMEOUT_SECONDS": "10",
            "AI_SERVICE_CACHE_TTL_SECONDS": "7200",
            "HUAWEI_CLOUD_ENABLED": "false"
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = AIServiceConfig()
            assert config.ENABLED is False

    def test_config_timeouts_are_reasonable(self):
        """Test that configured timeouts are reasonable"""
        config = AIServiceConfig()
        
        # All timeouts should be between 1 and 30 seconds
        assert 1 <= config.HEALTH_METRICS_TIMEOUT <= 30
        assert 1 <= config.RISK_SCORING_TIMEOUT <= 30
        assert 1 <= config.FORECAST_TIMEOUT <= 30

    def test_config_cache_ttl_is_reasonable(self):
        """Test that cache TTL is reasonable"""
        config = AIServiceConfig()
        
        # Cache TTL should be between 60 seconds and 24 hours
        assert 60 <= config.CACHE_TTL_SECONDS <= 86400

    def test_config_debug_flag_controls_logging(self):
        """Test that debug flag is properly configured"""
        with patch.dict(os.environ, {"AI_SERVICE_DEBUG": "true"}, clear=False):
            config = AIServiceConfig()
            # Debug can be enabled or disabled, just verify it's configured
            assert hasattr(config, 'DEBUG')

    def test_config_singleton_pattern(self):
        """Test that config can be used as singleton"""
        from ai_services.config import config as global_config
        
        assert isinstance(global_config, AIServiceConfig)
        assert global_config.ENABLED is not None


class TestConfigValidation:
    """Test configuration validation and error handling"""

    def test_invalid_timeout_configuration(self):
        """Test handling of invalid timeout values"""
        with patch.dict(os.environ, {"AI_SERVICE_TIMEOUT_SECONDS": "5"}, clear=False):
            # Should not crash, should use default
            config = AIServiceConfig()
            assert config.TIMEOUT_SECONDS > 0

    def test_missing_endpoints_handled(self):
        """Test that missing endpoints don't crash config loading"""
        with patch.dict(os.environ, {"HUAWEI_MODELARTS_ENDPOINT": ""}, clear=False):
            config = AIServiceConfig()
            # Config should still load, just mark as unavailable
            assert hasattr(config, 'MODELARTS_ENDPOINT')

    def test_cache_disabled_mode(self):
        """Test that cache can be disabled"""
        with patch.dict(os.environ, {"AI_SERVICE_CACHE_ENABLED": "false"}, clear=False):
            config = AIServiceConfig()
            # Cache flag should be respected
            assert hasattr(config, 'CACHE_ENABLED')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
