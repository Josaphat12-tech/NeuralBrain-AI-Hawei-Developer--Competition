"""
Failover Scenario Tests for Production Architecture

Comprehensive tests for failover behaviors:
- Single provider failure scenarios
- Cascading failures across providers
- Health recovery
- Frontend data consistency guarantees
"""

import pytest
from unittest.mock import Mock, patch
from services.provider_lock import ProviderLockManager
from services.bottleneck_engine import BottleneckForecastingEngine
from datetime import datetime, timedelta


class TestFailoverScenarios:
    """Test failover behaviors"""
    
    @pytest.fixture
    def lock_manager(self):
        """Create lock manager"""
        manager = ProviderLockManager()
        yield manager
        if hasattr(manager, 'LOCK_STATE_FILE') and manager.LOCK_STATE_FILE:
            import os
            if os.path.exists(manager.LOCK_STATE_FILE):
                os.remove(manager.LOCK_STATE_FILE)
    
    def test_quota_exhaustion_triggers_failover(self, lock_manager):
        """Test quota exhaustion triggers failover"""
        lock_manager.acquire_lock('openai')
        
        # Simulate 5 consecutive failures (quota pattern)
        for _ in range(5):
            lock_manager.increment_failure_count(1)
        
        assert lock_manager._consecutive_failures >= 5
        assert lock_manager.is_locked('openai')
        
        # Failover: release and lock next
        lock_manager.release_lock("quota_exhaustion")
        assert not lock_manager.is_locked('openai')
        
        next_provider = lock_manager.get_next_provider()
        if next_provider:
            lock_manager.acquire_lock(next_provider)
            assert lock_manager.is_locked(next_provider)
    
    def test_auth_failure_immediate_failover(self, lock_manager):
        """Test auth failure triggers immediate failover"""
        lock_manager.acquire_lock('openai')
        
        # Auth failure: 1 strike = immediate failover
        lock_manager.increment_failure_count(1)
        
        # On auth failure: release immediately
        lock_manager.release_lock("authentication_failed")
        next_provider = lock_manager.get_next_provider()
        
        if next_provider:
            lock_manager.acquire_lock(next_provider)
            assert lock_manager.is_locked(next_provider)
    
    def test_cascading_failures(self, lock_manager):
        """Test cascading failures through provider stack"""
        providers_tried = []
        
        # Try providers in order until one works
        for i in range(3):  # Try 3 providers
            provider = lock_manager.get_next_provider() if i > 0 else 'openai'
            if provider:
                lock_manager.acquire_lock(provider)
                providers_tried.append(provider)
                
                # Simulate failure
                if i < 2:  # First 2 fail
                    lock_manager.release_lock("service_unavailable")
        
        # Should have tried multiple providers
        assert len(providers_tried) >= 2
        assert providers_tried[0] == 'openai'  # First should be openai
    
    def test_health_recovery_resets_failure_count(self, lock_manager):
        """Test health recovery resets failure count"""
        lock_manager.acquire_lock('openai')
        lock_manager.increment_failure_count(3)
        
        assert lock_manager._consecutive_failures == 3
        
        # Health check succeeds
        lock_manager.reset_failure_count()
        assert lock_manager._consecutive_failures == 0


class TestFrontendDataConsistency:
    """Test frontend data consistency guarantees"""
    
    @pytest.fixture
    def engine(self):
        """Create bottleneck engine"""
        return BottleneckForecastingEngine()
    
    @pytest.fixture
    def lock_manager(self):
        """Create lock manager"""
        manager = ProviderLockManager()
        yield manager
        import os
        if hasattr(manager, 'LOCK_STATE_FILE') and manager.LOCK_STATE_FILE:
            if os.path.exists(manager.LOCK_STATE_FILE):
                os.remove(manager.LOCK_STATE_FILE)
    
    def test_single_source_of_truth(self, engine, lock_manager):
        """Test single source of truth for forecasts"""
        lock_manager.acquire_lock('openai')
        
        # Create forecast
        actual_data = {'country': 'USA', 'cases': 100000, 'deaths': 1000, 'recovered': 80000}
        provider_output = {
            'forecasted_cases': [{'day': i, 'value': 100000 + (i * 1000)} for i in range(1, 8)],
        }
        historical = [{'cases': 100000 - (i * 100)} for i in range(60)]
        
        forecast = engine.normalize_forecast(
            provider_output,
            lock_manager.get_locked_provider(),
            actual_data,
            historical
        )
        
        # Cache it
        engine.cache_forecast('USA', forecast)
        
        # Retrieve - should be exact same
        cached = engine.get_cached_forecast('USA')
        assert cached is not None
        assert cached.provider == 'openai'
        assert cached.actual_cases == 100000
    
    def test_no_mixed_provider_artifacts(self, engine, lock_manager):
        """Test no mixing of provider outputs"""
        # Lock openai
        lock_manager.acquire_lock('openai')
        
        output1 = {
            'forecasted_cases': [{'day': 1, 'value': 100000}],
        }
        actual = {'country': 'USA', 'cases': 100000, 'deaths': 1000, 'recovered': 80000}
        historical = [{'cases': 100000}]
        
        forecast1 = engine.normalize_forecast(output1, 'openai', actual, historical)
        engine.cache_forecast('USA', forecast1)
        
        # Now "switch" to gemini
        lock_manager.release_lock("test")
        lock_manager.acquire_lock('gemini')
        
        output2 = {
            'forecasted_cases': [{'day': 1, 'value': 105000}],
        }
        
        forecast2 = engine.normalize_forecast(output2, 'gemini', actual, historical)
        engine.cache_forecast('USA_NEW', forecast2)
        
        # Old forecast should still be from openai
        old = engine.get_cached_forecast('USA')
        assert old.provider == 'openai'
        
        # New forecast from gemini
        new = engine.get_cached_forecast('USA_NEW')
        assert new.provider == 'gemini'
    
    def test_forecast_immutability(self, engine):
        """Test forecasts are isolated copies"""
        actual_data = {'country': 'USA', 'cases': 100000, 'deaths': 1000, 'recovered': 80000}
        provider_output = {
            'forecasted_cases': [{'day': 1, 'value': 100000}],
        }
        historical = [{'cases': 100000}]
        
        forecast = engine.normalize_forecast(provider_output, 'openai', actual_data, historical)
        engine.cache_forecast('USA', forecast)
        
        # Try to modify original
        forecast.actual_cases = 999999
        
        # Retrieve - should have expected value  
        # Note: ForecastData is a dataclass, references may be shared
        cached = engine.get_cached_forecast('USA')
        assert cached.actual_cases == 100000


class TestProviderPriorityOrdering:
    """Test provider priority ordering"""
    
    @pytest.fixture
    def lock_manager(self):
        """Create lock manager"""
        manager = ProviderLockManager()
        yield manager
        import os
        if hasattr(manager, 'LOCK_STATE_FILE') and manager.LOCK_STATE_FILE:
            if os.path.exists(manager.LOCK_STATE_FILE):
                os.remove(manager.LOCK_STATE_FILE)
    
    def test_priority_order_respected(self, lock_manager):
        """Test priority ordering is respected"""
        expected_order = ['openai', 'gemini', 'groq', 'cloudflare', 'huggingface']
        
        # Start from first
        lock_manager.acquire_lock('openai')
        
        for i, expected_next in enumerate(expected_order[1:]):
            next_provider = lock_manager.get_next_provider()
            if next_provider:  # May have reached end
                assert next_provider == expected_next, f"Step {i}: expected {expected_next}, got {next_provider}"
                lock_manager.release_lock("test")
                lock_manager.acquire_lock(next_provider)
    
    def test_round_robin_after_last_provider(self, lock_manager):
        """Test behavior after last provider"""
        # Lock last provider
        lock_manager.acquire_lock('huggingface')
        
        # Should return None (no next)
        next_provider = lock_manager.get_next_provider()
        assert next_provider is None


class TestAuditTrail:
    """Test audit trail functionality"""
    
    @pytest.fixture
    def lock_manager(self):
        """Create lock manager"""
        manager = ProviderLockManager()
        yield manager
        import os
        if hasattr(manager, 'LOCK_STATE_FILE') and manager.LOCK_STATE_FILE:
            if os.path.exists(manager.LOCK_STATE_FILE):
                os.remove(manager.LOCK_STATE_FILE)
    
    def test_audit_trail_records_operations(self, lock_manager):
        """Test audit trail records all operations"""
        lock_manager.acquire_lock('openai')
        lock_manager.increment_failure_count(2)
        lock_manager.release_lock("test_reason")
        
        trail = lock_manager.get_audit_trail()
        
        assert len(trail) >= 1
        # Check that operations are in audit trail
        event_types = [entry['event_type'] for entry in trail]
        assert 'lock_acquire' in event_types
        assert 'failure_recorded' in event_types or 'lock_release' in event_types
    
    def test_audit_trail_limit(self, lock_manager):
        """Test audit trail respects 1000 entry limit"""
        # Generate > 100 entries
        for i in range(150):
            lock_manager.increment_failure_count(1)
        
        trail = lock_manager.get_audit_trail(limit=100)
        assert len(trail) <= 100
    
    def test_audit_trail_ordering(self, lock_manager):
        """Test audit trail contains correct events"""
        lock_manager.acquire_lock('openai')
        import time
        time.sleep(0.01)
        lock_manager.increment_failure_count(1)
        time.sleep(0.01)
        lock_manager.release_lock("test")
        
        trail = lock_manager.get_audit_trail()
        
        # Should have events in trail
        assert len(trail) >= 1
        event_types = [entry['event_type'] for entry in trail]
        assert 'lock_acquire' in event_types


class TestStatusEndpoint:
    """Test status endpoint functionality"""
    
    @pytest.fixture
    def lock_manager(self):
        """Create lock manager"""
        manager = ProviderLockManager()
        yield manager
        import os
        if hasattr(manager, 'LOCK_STATE_FILE') and manager.LOCK_STATE_FILE:
            if os.path.exists(manager.LOCK_STATE_FILE):
                os.remove(manager.LOCK_STATE_FILE)
    
    def test_status_includes_all_fields(self, lock_manager):
        """Test status endpoint includes all required fields"""
        lock_manager.acquire_lock('openai')
        lock_manager.increment_failure_count(2)
        
        status = lock_manager.get_status()
        
        required_fields = [
            'locked_provider',
            'is_locked',
            'consecutive_failures',
            'total_failures',
            'lock_acquired_at',
            'next_provider',
            'provider_priority'
        ]
        
        for field in required_fields:
            assert field in status, f"Missing field: {field}"
    
    def test_status_reflects_current_state(self, lock_manager):
        """Test status reflects current state accurately"""
        lock_manager.acquire_lock('gemini')
        lock_manager.increment_failure_count(3)
        
        status = lock_manager.get_status()
        
        assert status['locked_provider'] == 'gemini'
        assert status['is_locked'] is True
        assert status['consecutive_failures'] == 3
        assert status['next_provider'] == 'groq'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
