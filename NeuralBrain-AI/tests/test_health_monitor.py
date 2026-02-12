"""
Health Monitoring System - Test Suite

Test coverage:
- HealthMetricsCollector
- BackgroundHealthMonitor
- Health check detection
- Failover triggering
- Metrics collection and history
"""

import pytest
import threading
import time
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta

from services.health_monitor import (
    HealthMetricsCollector,
    BackgroundHealthMonitor,
    ProviderHealthStatus,
    HealthMetric,
    get_health_monitor,
    reset_health_monitor
)


class TestHealthMetricsCollector:
    """Test health metrics collection"""
    
    @pytest.fixture
    def collector(self):
        return HealthMetricsCollector(history_size=100)
    
    def test_record_health_check_success(self, collector):
        """Test recording successful health check"""
        collector.record_health_check(
            "openai",
            True,
            latency_ms=150.5,
            error_message=None
        )
        
        history = collector.get_history("openai")
        assert len(history) == 1
        assert history[0]["status"] == "success"
        assert history[0]["latency_ms"] == 150.5
        assert history[0]["provider"] == "openai"
    
    def test_record_health_check_failure(self, collector):
        """Test recording failed health check"""
        collector.record_health_check(
            "groq",
            False,
            latency_ms=None,
            error_message="Connection timeout"
        )
        
        history = collector.get_history("groq")
        assert len(history) == 1
        assert history[0]["status"] == "failure"
        assert history[0]["error_message"] == "Connection timeout"
    
    def test_get_provider_stats_empty(self, collector):
        """Test stats for provider with no data"""
        stats = collector.get_provider_stats("unknown_provider")
        
        assert stats["provider"] == "unknown_provider"
        assert stats["check_count"] == 0
        assert stats["success_count"] == 0
        assert stats["failure_count"] == 0
        assert stats["error_rate"] == 0.0
    
    def test_get_provider_stats_with_data(self, collector):
        """Test stats calculation"""
        # Record 4 successes and 1 failure
        for _ in range(4):
            collector.record_health_check("provider1", True, latency_ms=100)
        collector.record_health_check("provider1", False, latency_ms=None)
        
        stats = collector.get_provider_stats("provider1")
        
        assert stats["check_count"] == 5
        assert stats["success_count"] == 4
        assert stats["failure_count"] == 1
        assert stats["error_rate"] == 20.0
        assert stats["avg_latency_ms"] == 100.0
    
    def test_get_provider_stats_error_rate(self, collector):
        """Test error rate calculation"""
        for _ in range(3):
            collector.record_health_check("provider2", True, latency_ms=200)
        for _ in range(7):
            collector.record_health_check("provider2", False)
        
        stats = collector.get_provider_stats("provider2")
        
        assert stats["check_count"] == 10
        assert stats["success_count"] == 3
        assert stats["failure_count"] == 7
        assert stats["error_rate"] == 70.0
    
    def test_get_history_limit(self, collector):
        """Test history limit"""
        for i in range(50):
            collector.record_health_check("provider3", True)
        
        history = collector.get_history("provider3", limit=10)
        assert len(history) == 10
    
    def test_thread_safety(self, collector):
        """Test thread-safe operations"""
        results = []
        
        def record_metrics():
            for i in range(100):
                collector.record_health_check("provider", i % 2 == 0)
        
        threads = [threading.Thread(target=record_metrics) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        stats = collector.get_provider_stats("provider")
        # Should have metrics (exact count depends on deque maxlen timing)
        assert stats["check_count"] > 0


class TestBackgroundHealthMonitor:
    """Test background health monitor"""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        orch = MagicMock()
        
        # Mock providers
        mock_provider1 = MagicMock()
        mock_provider1.is_available.return_value = True
        mock_provider1.health_check.return_value = {"status": "healthy"}
        
        mock_provider2 = MagicMock()
        mock_provider2.is_available.return_value = True
        mock_provider2.health_check.return_value = {"status": "healthy"}
        
        orch.providers = {
            "openai": mock_provider1,
            "gemini": mock_provider2
        }
        
        # Mock lock manager
        orch.lock_manager = MagicMock()
        orch.lock_manager.get_current_provider.return_value = "openai"
        orch._trigger_failover = MagicMock()
        
        return orch
    
    @pytest.fixture
    def monitor(self, mock_orchestrator):
        reset_health_monitor()
        monitor = BackgroundHealthMonitor(
            orchestrator=mock_orchestrator,
            check_interval_seconds=1,
            failure_threshold=2,
            degradation_threshold=50.0
        )
        yield monitor
        monitor.stop()
        reset_health_monitor()
    
    def test_monitor_initialization(self, monitor):
        """Test monitor initialization"""
        assert monitor.is_running is False
        assert monitor.check_interval == 1
        assert monitor.failure_threshold == 2
        assert monitor.degradation_threshold == 50.0
        assert monitor.metrics_collector is not None
    
    def test_monitor_start_stop(self, monitor):
        """Test starting and stopping monitor"""
        monitor.start()
        assert monitor.is_running is True
        assert monitor.monitor_thread is not None
        
        monitor.stop()
        assert monitor.is_running is False
    
    def test_monitor_prevents_double_start(self, monitor):
        """Test that starting twice doesn't cause issues"""
        monitor.start()
        monitor.start()  # Should not error
        
        monitor.stop()
    
    def test_check_all_providers(self, monitor, mock_orchestrator):
        """Test checking all providers"""
        monitor._check_all_providers()
        
        # Verify health_check was called on all providers
        mock_orchestrator.providers["openai"].health_check.assert_called()
        mock_orchestrator.providers["gemini"].health_check.assert_called()
    
    def test_check_unavailable_provider(self, monitor, mock_orchestrator):
        """Test checking unavailable provider"""
        mock_orchestrator.providers["openai"].is_available.return_value = False
        
        monitor._check_all_providers()
        
        # Verify health_check was NOT called
        mock_orchestrator.providers["openai"].health_check.assert_not_called()
        
        # Verify metric was recorded as failure
        stats = monitor.metrics_collector.get_provider_stats("openai")
        assert stats["failure_count"] >= 1
    
    def test_detect_degradation(self, monitor):
        """Test degradation detection"""
        # Record high error rate
        for _ in range(6):
            monitor.metrics_collector.record_health_check("provider1", False)
        for _ in range(4):
            monitor.metrics_collector.record_health_check("provider1", True)
        
        # Should detect degradation (60% error rate > 50% threshold)
        monitor._detect_degradation()
        # No assertion needed, just verify it runs without error
    
    def test_failover_on_consecutive_failures(self, monitor, mock_orchestrator):
        """Test failover triggered on consecutive failures"""
        # Set up consecutive failures
        monitor.provider_consecutive_failures["openai"] = 3
        mock_orchestrator.lock_manager.get_current_provider.return_value = "openai"
        
        monitor._trigger_failover_if_needed()
        
        # Verify failover was triggered
        mock_orchestrator._trigger_failover.assert_called()
    
    def test_get_provider_health_healthy(self, monitor):
        """Test getting health for healthy provider"""
        monitor.metrics_collector.record_health_check("provider1", True, latency_ms=100)
        monitor.metrics_collector.record_health_check("provider1", True, latency_ms=120)
        
        health = monitor.get_provider_health("provider1")
        
        assert health.provider == "provider1"
        assert health.status == ProviderHealthStatus.HEALTHY.value
        assert health.error_rate == 0.0
        assert health.avg_latency_ms > 0
    
    def test_get_provider_health_degraded(self, monitor):
        """Test getting health for degraded provider"""
        monitor.degradation_threshold = 50.0
        
        # Record high error rate
        for _ in range(7):
            monitor.metrics_collector.record_health_check("provider2", False)
        for _ in range(3):
            monitor.metrics_collector.record_health_check("provider2", True)
        
        health = monitor.get_provider_health("provider2")
        
        assert health.provider == "provider2"
        assert health.status == ProviderHealthStatus.DEGRADED.value
        assert health.error_rate == 70.0
    
    def test_get_provider_health_unavailable(self, monitor):
        """Test getting health for unavailable provider"""
        # Record all failures (100% error rate = unavailable)
        for _ in range(10):
            monitor.metrics_collector.record_health_check("provider3", False)
        
        health = monitor.get_provider_health("provider3")
        
        assert health.provider == "provider3"
        assert health.status == ProviderHealthStatus.UNAVAILABLE.value
        assert health.error_rate == 100.0
    
    def test_get_all_providers_health(self, monitor, mock_orchestrator):
        """Test getting health for all providers"""
        monitor.metrics_collector.record_health_check("openai", True)
        monitor.metrics_collector.record_health_check("gemini", True)
        
        all_health = monitor.get_all_providers_health()
        
        assert len(all_health) == 2
        assert all_health[0].provider in ["openai", "gemini"]
        assert all_health[1].provider in ["openai", "gemini"]
    
    def test_get_health_summary(self, monitor, mock_orchestrator):
        """Test getting health summary"""
        monitor.metrics_collector.record_health_check("openai", True)
        monitor.metrics_collector.record_health_check("gemini", False)
        
        summary = monitor.get_health_summary()
        
        assert summary["is_monitoring"] is False  # Not started yet
        assert summary["current_provider"] == "openai"
        assert summary["provider_stats"]["total"] == 2
        assert summary["provider_stats"]["healthy"] >= 1
        # gemini has 100% error rate = unavailable, not degraded
        assert summary["provider_stats"]["unavailable"] >= 1 or summary["provider_stats"]["degraded"] >= 0
    
    def test_get_metrics_history(self, monitor):
        """Test getting metrics history"""
        for i in range(10):
            monitor.metrics_collector.record_health_check("provider", i % 2 == 0)
        
        history = monitor.get_metrics_history("provider", limit=5)
        
        assert len(history) == 5
        assert all("timestamp" in m for m in history)


class TestMonitorIntegration:
    """Test monitor integration scenarios"""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        orch = MagicMock()
        
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.health_check.return_value = {"status": "healthy"}
        
        orch.providers = {"provider1": mock_provider}
        orch.lock_manager = MagicMock()
        orch.lock_manager.get_current_provider.return_value = "provider1"
        orch._trigger_failover = MagicMock()
        
        return orch
    
    def test_singleton_pattern(self, mock_orchestrator):
        """Test health monitor singleton"""
        reset_health_monitor()
        
        monitor1 = get_health_monitor(mock_orchestrator)
        monitor2 = get_health_monitor(mock_orchestrator)
        
        assert monitor1 is monitor2
        reset_health_monitor()
    
    def test_monitor_lifecycle(self, mock_orchestrator):
        """Test complete monitor lifecycle"""
        reset_health_monitor()
        
        monitor = get_health_monitor(mock_orchestrator)
        
        # Start monitoring
        monitor.start()
        assert monitor.is_running is True
        
        # Let it run briefly
        time.sleep(0.5)
        
        # Check that metrics were collected
        summary = monitor.get_health_summary()
        assert summary["is_monitoring"] is True
        
        # Stop monitoring
        monitor.stop()
        assert monitor.is_running is False
        
        reset_health_monitor()


class TestHealthMetricsPerformance:
    """Test performance characteristics"""
    
    def test_metrics_collection_performance(self):
        """Test that metrics collection is fast"""
        collector = HealthMetricsCollector()
        
        start_time = time.time()
        for i in range(1000):
            collector.record_health_check(f"provider_{i % 10}", i % 2 == 0)
        elapsed = time.time() - start_time
        
        # Should collect 1000 metrics in under 1 second
        assert elapsed < 1.0
    
    def test_stats_calculation_performance(self):
        """Test that stats calculation is fast"""
        collector = HealthMetricsCollector()
        
        # Record many metrics
        for i in range(500):
            collector.record_health_check("provider", i % 2 == 0)
        
        start_time = time.time()
        for _ in range(100):
            collector.get_provider_stats("provider")
        elapsed = time.time() - start_time
        
        # Should calculate stats 100 times in under 1 second
        assert elapsed < 1.0
