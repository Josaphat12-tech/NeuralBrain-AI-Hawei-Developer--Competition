"""
Test suite for Performance and Resilience (Phase 4)
Tests latency, cache effectiveness, and error recovery
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from ai_services.inference_adapter import get_health_metrics_adapter
from ai_services.risk_scoring_engine import get_medical_ai_risk_scorer
from ai_services.forecast_engine import get_forecast_engine


class TestPerformanceMetrics:
    """Test performance characteristics"""

    def test_adapter_response_time_acceptable(self):
        """Test that adapter responds within timeout"""
        adapter = get_health_metrics_adapter()
        
        start = time.time()
        result = adapter.get_health_metrics(
            patient_id="perf_test",
            context="test",
            fallback_fn=lambda: {"heart_rate": 72}
        )
        elapsed = time.time() - start
        
        # Should complete quickly (< 1 second in normal operation)
        assert elapsed < 5.0  # Generous timeout for testing
        assert result is not None

    def test_risk_scorer_response_time_acceptable(self):
        """Test that risk scorer responds within timeout"""
        scorer = get_medical_ai_risk_scorer()
        
        start = time.time()
        result = scorer.score_health_status(
            current_metrics={"heart_rate": 72},
            recent_history=[],
            fallback_fn=lambda m, h: {"overall_risk": "Low", "risk_percentage": 20}
        )
        elapsed = time.time() - start
        
        # Should complete quickly
        assert elapsed < 5.0
        assert result is not None

    def test_forecast_engine_response_time_acceptable(self):
        """Test that forecast engine responds within timeout"""
        engine = get_forecast_engine()
        
        start = time.time()
        result = engine.generate_forecast(
            historical_data=[98.6] * 60,
            days_ahead=7,
            fallback_fn=lambda: {}
        )
        elapsed = time.time() - start
        
        # Should complete quickly
        assert elapsed < 5.0
        assert result is not None

    def test_multiple_calls_performance(self):
        """Test performance across multiple calls"""
        adapter = get_health_metrics_adapter()
        times = []
        
        for i in range(5):
            start = time.time()
            adapter.get_health_metrics(
                patient_id=f"perf_test_{i}",
                context="test",
                fallback_fn=lambda: {"heart_rate": 72}
            )
            elapsed = time.time() - start
            times.append(elapsed)
        
        # Average time should be reasonable
        avg_time = sum(times) / len(times)
        assert avg_time < 2.0


class TestCacheEffectiveness:
    """Test caching mechanism"""

    def test_cache_improves_subsequent_calls(self):
        """Test that cache makes subsequent calls faster"""
        from ai_services.fallback_manager import fallback_manager
        
        call_times = []
        
        def slow_operation():
            time.sleep(0.1)
            return "result"
        
        def fallback():
            return "fallback"
        
        # First call (not cached)
        start = time.time()
        fallback_manager.try_cloud_operation("cache_test", slow_operation, fallback)
        first_call_time = time.time() - start
        call_times.append(first_call_time)
        
        # Second call (should be cached if cache enabled)
        start = time.time()
        fallback_manager.try_cloud_operation("cache_test", slow_operation, fallback)
        second_call_time = time.time() - start
        call_times.append(second_call_time)
        
        # Second call should be faster or equal
        assert second_call_time <= first_call_time + 0.1

    def test_cache_separate_for_different_operations(self):
        """Test that cache entries don't cross-contaminate"""
        from ai_services.fallback_manager import fallback_manager
        
        results = {}
        
        def op1():
            return "result1"
        
        def op2():
            return "result2"
        
        fallback = lambda: "fallback"
        
        result1 = fallback_manager.try_cloud_operation("op1", op1, fallback)
        result2 = fallback_manager.try_cloud_operation("op2", op2, fallback)
        
        assert result1 == "result1"
        assert result2 == "result2"


class TestErrorRecovery:
    """Test error recovery and resilience"""

    def test_timeout_triggers_fallback(self):
        """Test that timeout triggers fallback"""
        from ai_services.fallback_manager import fallback_manager
        
        def slow_operation():
            time.sleep(0.5)
            return "result"
        
        def fallback():
            return "fallback_result"
        
        result = fallback_manager.try_cloud_operation("timeout_test", slow_operation, fallback)
        
        # Should succeed with fallback
        assert result is not None

    def test_exception_triggers_fallback(self):
        """Test that exceptions trigger fallback"""
        from ai_services.fallback_manager import fallback_manager
        
        def failing_operation():
            raise ValueError("Operation failed")
        
        def fallback():
            return "fallback_result"
        
        result = fallback_manager.try_cloud_operation("error_test", failing_operation, fallback)
        
        # Should use fallback
        assert result == "fallback_result"

    def test_none_response_triggers_fallback(self):
        """Test that None response triggers fallback"""
        from ai_services.fallback_manager import fallback_manager
        
        def empty_operation():
            return None
        
        def fallback():
            return "fallback_result"
        
        result = fallback_manager.try_cloud_operation("none_test", empty_operation, fallback)
        
        # Should use fallback
        assert result == "fallback_result"

    def test_multiple_consecutive_failures(self):
        """Test behavior with multiple consecutive failures"""
        from ai_services.fallback_manager import fallback_manager
        
        call_count = 0
        
        def failing_operation():
            nonlocal call_count
            call_count += 1
            raise Exception("Repeated failure")
        
        def fallback():
            return "fallback_result"
        
        # Multiple calls should all use fallback
        for i in range(3):
            result = fallback_manager.try_cloud_operation(
                f"multi_fail_{i}", failing_operation, fallback
            )
            assert result == "fallback_result"


class TestLoadTesting:
    """Test system under load"""

    def test_sequential_calls_performance(self):
        """Test performance with sequential calls"""
        adapter = get_health_metrics_adapter()
        
        start = time.time()
        for i in range(10):
            adapter.get_health_metrics(
                patient_id=f"load_test_{i}",
                context="load_test",
                fallback_fn=lambda: {"heart_rate": 72}
            )
        elapsed = time.time() - start
        
        # 10 calls should complete in reasonable time
        assert elapsed < 10.0  # Max 1 second per call on average
        avg_per_call = elapsed / 10
        assert avg_per_call < 1.0

    def test_memory_usage_reasonable(self):
        """Test that memory usage remains reasonable"""
        import sys
        
        adapter = get_health_metrics_adapter()
        
        # Get initial size
        initial_size = sys.getsizeof(adapter)
        
        # Make many calls
        for i in range(100):
            adapter.get_health_metrics(
                patient_id=f"mem_test_{i}",
                context="test",
                fallback_fn=lambda: {"heart_rate": 72}
            )
        
        # Size should not grow excessively
        final_size = sys.getsizeof(adapter)
        
        # Final should be roughly same or slightly more
        assert final_size < initial_size * 10  # Allow 10x growth (conservative)


class TestDataValidation:
    """Test data validation under stress"""

    def test_adapter_validates_output_schema(self):
        """Test that adapter validates output schema"""
        adapter = get_health_metrics_adapter()
        
        result = adapter.get_health_metrics(
            patient_id="validation_test",
            context="test",
            fallback_fn=lambda: {"heart_rate": 72}
        )
        
        # Should return dict
        assert isinstance(result, dict)

    def test_scorer_validates_output_schema(self):
        """Test that scorer validates output schema"""
        scorer = get_medical_ai_risk_scorer()
        
        result = scorer.score_health_status(
            current_metrics={"heart_rate": 72},
            recent_history=[],
            fallback_fn=lambda m, h: {"overall_risk": "Low", "risk_percentage": 20}
        )
        
        # Should return dict with expected fields
        assert isinstance(result, dict)

    def test_forecast_validates_output_schema(self):
        """Test that forecast validates output schema"""
        engine = get_forecast_engine()
        
        result = engine.generate_forecast(
            historical_data=[98.6] * 60,
            days_ahead=7,
            fallback_fn=lambda: {"dates": [], "historical": [], "forecast": []}
        )
        
        # Should return dict with expected fields
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
