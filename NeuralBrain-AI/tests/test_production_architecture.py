"""
Test Suite: Provider Lock System & Bottleneck Engine

Comprehensive tests for:
- Provider lock acquire/release
- Lock persistence
- Failure tracking
- Forecast normalization
- Risk assessment
- Confidence calculation
"""

import pytest
import json
import os
import tempfile
from datetime import datetime, timedelta
from services.provider_lock import ProviderLockManager, get_provider_lock_manager
from services.bottleneck_engine import BottleneckForecastingEngine, get_bottleneck_engine, ForecastData


class TestProviderLockManager:
    """Tests for ProviderLockManager"""
    
    @pytest.fixture
    def lock_manager(self):
        """Create lock manager instance"""
        manager = ProviderLockManager()
        yield manager
        # Cleanup
        if os.path.exists(manager.LOCK_STATE_FILE):
            os.remove(manager.LOCK_STATE_FILE)
    
    def test_acquire_lock_openai(self, lock_manager):
        """Test acquiring lock for OpenAI"""
        assert lock_manager.acquire_lock('openai')
        assert lock_manager.get_locked_provider() == 'openai'
        assert lock_manager.is_locked('openai')
        assert not lock_manager.is_locked('gemini')
    
    def test_acquire_lock_invalid_provider(self, lock_manager):
        """Test acquiring lock for invalid provider"""
        assert not lock_manager.acquire_lock('invalid_provider')
        assert lock_manager.get_locked_provider() is None
    
    def test_release_lock(self, lock_manager):
        """Test releasing lock"""
        lock_manager.acquire_lock('openai')
        assert lock_manager.get_locked_provider() == 'openai'
        
        assert lock_manager.release_lock("test_release")
        assert lock_manager.get_locked_provider() is None
    
    def test_lock_switch(self, lock_manager):
        """Test switching locks"""
        lock_manager.acquire_lock('openai')
        assert lock_manager.is_locked('openai')
        
        lock_manager.acquire_lock('gemini')
        assert lock_manager.is_locked('gemini')
        assert not lock_manager.is_locked('openai')
    
    def test_increment_failure_count(self, lock_manager):
        """Test incrementing failure count"""
        lock_manager.acquire_lock('openai')
        
        count = lock_manager.increment_failure_count(1)
        assert count == 1
        
        count = lock_manager.increment_failure_count(2)
        assert count == 3
    
    def test_reset_failure_count(self, lock_manager):
        """Test resetting failure count"""
        lock_manager.acquire_lock('openai')
        lock_manager.increment_failure_count(5)
        assert lock_manager._consecutive_failures == 5
        
        lock_manager.reset_failure_count()
        assert lock_manager._consecutive_failures == 0
    
    def test_get_next_provider(self, lock_manager):
        """Test getting next provider in priority"""
        lock_manager.acquire_lock('openai')
        assert lock_manager.get_next_provider() == 'gemini'
        
        lock_manager.acquire_lock('gemini')
        assert lock_manager.get_next_provider() == 'groq'
        
        lock_manager.acquire_lock('huggingface')
        assert lock_manager.get_next_provider() is None
    
    def test_get_status(self, lock_manager):
        """Test getting lock status"""
        lock_manager.acquire_lock('openai')
        lock_manager.increment_failure_count(2)
        
        status = lock_manager.get_status()
        assert status['locked_provider'] == 'openai'
        assert status['consecutive_failures'] == 2
        assert status['total_failures'] == 2
        assert status['is_locked'] is True
        assert status['next_provider'] == 'gemini'
    
    def test_audit_trail(self, lock_manager):
        """Test audit trail logging"""
        lock_manager.acquire_lock('openai')
        lock_manager.increment_failure_count(1)
        lock_manager.release_lock("test_reason")
        
        trail = lock_manager.get_audit_trail()
        assert len(trail) >= 3
        assert trail[0]['event_type'] == 'lock_acquire'
        assert trail[1]['event_type'] == 'failure_recorded'
        assert trail[2]['event_type'] == 'lock_release'
    
    def test_lock_persistence(self, lock_manager):
        """Test lock state persistence"""
        lock_manager.acquire_lock('openai')
        lock_manager.increment_failure_count(3)
        
        # Create new instance - should load state
        new_manager = ProviderLockManager()
        assert new_manager.get_locked_provider() == 'openai'
        assert new_manager._consecutive_failures == 3
    
    def test_thread_safety(self, lock_manager):
        """Test thread-safe operations"""
        import threading
        
        results = []
        
        def acquire_and_fail():
            if lock_manager.acquire_lock('openai'):
                results.append('acquired')
        
        threads = [threading.Thread(target=acquire_and_fail) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should still have only one lock
        assert lock_manager.is_locked('openai')


class TestBottleneckForecastingEngine:
    """Tests for BottleneckForecastingEngine"""
    
    @pytest.fixture
    def engine(self):
        """Create bottleneck engine"""
        return BottleneckForecastingEngine()
    
    @pytest.fixture
    def sample_actual_data(self):
        """Sample actual data"""
        return {
            'country': 'USA',
            'cases': 100000,
            'deaths': 1000,
            'recovered': 80000
        }
    
    @pytest.fixture
    def sample_forecast_output(self):
        """Sample AI provider output"""
        return {
            'forecasted_cases': [
                {'day': 1, 'value': 105000},
                {'day': 2, 'value': 110000},
                {'day': 3, 'value': 115000},
                {'day': 4, 'value': 120000},
                {'day': 5, 'value': 125000},
                {'day': 6, 'value': 130000},
                {'day': 7, 'value': 135000}
            ],
            'forecasted_deaths': [
                {'day': 1, 'value': 1050},
                {'day': 7, 'value': 1350}
            ]
        }
    
    @pytest.fixture
    def sample_historical_data(self):
        """Sample historical data"""
        data = []
        base_cases = 50000
        for i in range(60):
            data.append({
                'date': (datetime.utcnow() - timedelta(days=60-i)).isoformat(),
                'cases': base_cases + (i * 500),
                'deaths': (base_cases + (i * 500)) // 100
            })
        return data
    
    def test_normalize_forecast(self, engine, sample_actual_data, sample_forecast_output, sample_historical_data):
        """Test forecast normalization"""
        forecast = engine.normalize_forecast(
            sample_forecast_output,
            'openai',
            sample_actual_data,
            sample_historical_data
        )
        
        assert isinstance(forecast, ForecastData)
        assert forecast.region == 'USA'
        assert forecast.actual_cases == 100000
        assert forecast.provider == 'openai'
        assert len(forecast.forecasted_cases) == 7
        assert 0 < forecast.confidence_score < 1
        assert 0 < forecast.risk_score <= 100
    
    def test_extract_cases_forecast(self, engine, sample_forecast_output):
        """Test cases forecast extraction"""
        cases = engine._extract_cases_forecast(sample_forecast_output)
        assert len(cases) == 7
        assert cases[0]['day'] == 1
        assert cases[-1]['value'] == 135000
    
    def test_confidence_calculation(self, engine, sample_actual_data, sample_forecast_output, sample_historical_data):
        """Test confidence score calculation"""
        conf_openai = engine._calculate_confidence(
            sample_forecast_output['forecasted_cases'],
            sample_actual_data,
            sample_historical_data,
            'openai'
        )
        
        conf_gemini = engine._calculate_confidence(
            sample_forecast_output['forecasted_cases'],
            sample_actual_data,
            sample_historical_data,
            'gemini'
        )
        
        # OpenAI should have slightly higher confidence
        assert 0.5 < conf_openai <= 0.98
        assert 0.5 < conf_gemini <= 0.98
    
    def test_risk_assessment_high_growth(self, engine):
        """Test risk assessment for high growth"""
        actual_data = {'cases': 100000, 'deaths': 1000}
        forecasts = [
            {'day': i, 'value': 100000 * (1.15 ** i)}
            for i in range(1, 8)
        ]
        historical = [{'cases': 50000 * i} for i in range(1, 11)]
        
        risk_level, risk_score = engine._assess_risk(forecasts, actual_data, historical)
        assert risk_level == 'RED'
        assert risk_score > 50
    
    def test_risk_assessment_low_growth(self, engine):
        """Test risk assessment for low growth"""
        actual_data = {'cases': 100000, 'deaths': 1000}
        forecasts = [
            {'day': i, 'value': 100000 * (1.005 ** i)}
            for i in range(1, 8)
        ]
        historical = [{'cases': 100000} for _ in range(10)]
        
        risk_level, risk_score = engine._assess_risk(forecasts, actual_data, historical)
        assert risk_level == 'GREEN'
        assert risk_score < 50
    
    def test_outbreak_probability_high(self, engine):
        """Test outbreak probability for high growth"""
        actual_data = {'cases': 100000}
        forecasts = [{'day': 7, 'value': 150000}]
        historical = []
        
        prob = engine._calculate_outbreak_probability(forecasts, actual_data, historical)
        assert prob > 0.5
    
    def test_outbreak_probability_low(self, engine):
        """Test outbreak probability for low growth"""
        actual_data = {'cases': 100000}
        forecasts = [{'day': 7, 'value': 100500}]
        historical = []
        
        prob = engine._calculate_outbreak_probability(forecasts, actual_data, historical)
        assert prob < 0.5
    
    def test_trend_determination_increasing(self, engine):
        """Test trend determination for increasing"""
        actual_data = {'cases': 100000}
        forecasts = [{'day': 7, 'value': 120000}]
        historical = []
        
        trend = engine._determine_trend(forecasts, actual_data, historical)
        assert trend == 'increasing'
    
    def test_trend_determination_decreasing(self, engine):
        """Test trend determination for decreasing"""
        actual_data = {'cases': 100000}
        forecasts = [{'day': 7, 'value': 80000}]
        historical = []
        
        trend = engine._determine_trend(forecasts, actual_data, historical)
        assert trend == 'decreasing'
    
    def test_trend_determination_stable(self, engine):
        """Test trend determination for stable"""
        actual_data = {'cases': 100000}
        forecasts = [{'day': 7, 'value': 101000}]
        historical = []
        
        trend = engine._determine_trend(forecasts, actual_data, historical)
        assert trend == 'stable'
    
    def test_cache_forecast(self, engine, sample_actual_data, sample_forecast_output, sample_historical_data):
        """Test forecast caching"""
        forecast = engine.normalize_forecast(
            sample_forecast_output,
            'openai',
            sample_actual_data,
            sample_historical_data
        )
        
        engine.cache_forecast('USA', forecast)
        cached = engine.get_cached_forecast('USA')
        assert cached is not None
        assert cached.region == 'USA'
    
    def test_clear_cache(self, engine, sample_actual_data, sample_forecast_output, sample_historical_data):
        """Test cache clearing"""
        forecast = engine.normalize_forecast(
            sample_forecast_output,
            'openai',
            sample_actual_data,
            sample_historical_data
        )
        
        engine.cache_forecast('USA', forecast)
        assert len(engine.get_all_cached_forecasts()) > 0
        
        engine.clear_cache()
        assert len(engine.get_all_cached_forecasts()) == 0
    
    def test_forecast_to_dict(self, engine, sample_actual_data, sample_forecast_output, sample_historical_data):
        """Test ForecastData conversion to dict"""
        forecast = engine.normalize_forecast(
            sample_forecast_output,
            'openai',
            sample_actual_data,
            sample_historical_data
        )
        
        data_dict = forecast.to_dict()
        assert isinstance(data_dict, dict)
        assert data_dict['region'] == 'USA'
        assert data_dict['provider'] == 'openai'
        assert 'timestamp' in data_dict


class TestProviderLockAndBottleneckIntegration:
    """Integration tests for lock + bottleneck"""
    
    def test_locked_provider_feeds_bottleneck(self):
        """Test that locked provider's output goes through bottleneck"""
        lock_mgr = ProviderLockManager()
        engine = BottleneckForecastingEngine()
        
        # Lock OpenAI
        lock_mgr.acquire_lock('openai')
        
        # Simulate forecast
        actual_data = {'country': 'USA', 'cases': 100000, 'deaths': 1000, 'recovered': 80000}
        provider_output = {
            'forecasted_cases': [{'day': i, 'value': 100000 + (i * 1000)} for i in range(1, 8)],
            'forecasted_deaths': []
        }
        historical = [{'cases': 100000 - (i * 1000)} for i in range(60)]
        
        # Normalize through bottleneck
        forecast = engine.normalize_forecast(
            provider_output,
            lock_mgr.get_locked_provider(),
            actual_data,
            historical
        )
        
        assert forecast.provider == 'openai'
        assert lock_mgr.is_locked('openai')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
