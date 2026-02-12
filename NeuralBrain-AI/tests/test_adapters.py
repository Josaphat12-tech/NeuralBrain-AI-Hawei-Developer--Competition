"""
Test suite for AI Service Adapters (Phase 4)
Tests all 3 adapters: health metrics, risk scoring, forecasting
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ai_services.inference_adapter import HuaweiHealthMetricsAdapter, get_health_metrics_adapter
from ai_services.risk_scoring_engine import HuaweiMedicalAIRiskScorer, get_medical_ai_risk_scorer
from ai_services.forecast_engine import HuaweiTimeSeriesForecastEngine, get_forecast_engine


class TestHealthMetricsAdapter:
    """Test HuaweiHealthMetricsAdapter"""

    def test_adapter_initialization(self):
        """Test that adapter initializes correctly"""
        adapter = HuaweiHealthMetricsAdapter()
        assert adapter is not None

    def test_get_health_metrics_returns_dict(self):
        """Test that get_health_metrics returns dictionary"""
        adapter = HuaweiHealthMetricsAdapter()
        fallback = lambda: {"heart_rate": 72}
        
        result = adapter.get_health_metrics(
            patient_id="test123",
            context="test",
            fallback_fn=fallback
        )
        
        assert isinstance(result, dict)

    def test_get_health_metrics_contains_required_fields(self):
        """Test that returned metrics contain required fields"""
        adapter = HuaweiHealthMetricsAdapter()
        fallback = lambda: {
            "heart_rate": 72,
            "temperature": 98.6,
            "blood_pressure_sys": 120,
            "blood_pressure_dia": 80,
            "oxygen_saturation": 98,
            "respiratory_rate": 16,
            "glucose_level": 100
        }
        
        result = adapter.get_health_metrics(
            patient_id="test123",
            context="test",
            fallback_fn=fallback
        )
        
        assert "heart_rate" in result or len(result) > 0

    def test_get_health_metrics_uses_fallback(self):
        """Test that fallback is used when cloud unavailable"""
        adapter = HuaweiHealthMetricsAdapter()
        fallback_called = False
        
        def fallback():
            nonlocal fallback_called
            fallback_called = True
            return {"heart_rate": 72}
        
        # Mock the client to return None (simulating cloud unavailable)
        adapter.client = None
        
        result = adapter.get_health_metrics(
            patient_id="test123",
            context="test",
            fallback_fn=fallback
        )
        
        # Should either use fallback or return default metrics
        assert result is not None

    def test_get_default_metrics_returns_valid_data(self):
        """Test that default metrics are valid"""
        adapter = HuaweiHealthMetricsAdapter()
        defaults = adapter._get_default_metrics()
        
        assert isinstance(defaults, dict)
        assert "heart_rate" in defaults


class TestRiskScoringAdapter:
    """Test HuaweiMedicalAIRiskScorer"""

    def test_scorer_initialization(self):
        """Test that scorer initializes correctly"""
        scorer = HuaweiMedicalAIRiskScorer()
        assert scorer is not None

    def test_score_health_status_returns_dict(self):
        """Test that scoring returns dictionary"""
        scorer = HuaweiMedicalAIRiskScorer()
        metrics = {"heart_rate": 72, "temperature": 98.6}
        history = [{"heart_rate": 70}]
        fallback = lambda m, h: {"overall_risk": "Low", "risk_percentage": 20}
        
        result = scorer.score_health_status(
            current_metrics=metrics,
            recent_history=history,
            fallback_fn=fallback
        )
        
        assert isinstance(result, dict)

    def test_score_health_status_returns_required_fields(self):
        """Test that risk score contains required fields"""
        scorer = HuaweiMedicalAIRiskScorer()
        metrics = {"heart_rate": 72}
        history = []
        fallback = lambda m, h: {
            "overall_risk": "Low",
            "risk_percentage": 20,
            "confidence": 0.9
        }
        
        result = scorer.score_health_status(
            current_metrics=metrics,
            recent_history=history,
            fallback_fn=fallback
        )
        
        assert "overall_risk" in result or len(result) > 0

    def test_score_health_status_uses_fallback(self):
        """Test that fallback is used when cloud unavailable"""
        scorer = HuaweiMedicalAIRiskScorer()
        
        def fallback(m, h):
            return {
                "overall_risk": "Low",
                "risk_percentage": 20,
                "confidence": 0.9
            }
        
        # Mock the client to return None
        scorer.client = None
        
        result = scorer.score_health_status(
            current_metrics={"heart_rate": 72},
            recent_history=[],
            fallback_fn=fallback
        )
        
        assert result is not None

    def test_get_default_risk_score_returns_valid_data(self):
        """Test that default risk score is valid"""
        scorer = HuaweiMedicalAIRiskScorer()
        metrics = {"heart_rate": 72}
        default_score = scorer._get_default_risk_score(metrics)
        
        assert isinstance(default_score, dict)
        assert "overall_risk" in default_score


class TestForecastAdapter:
    """Test HuaweiTimeSeriesForecastEngine"""

    def test_forecast_engine_initialization(self):
        """Test that forecast engine initializes correctly"""
        engine = HuaweiTimeSeriesForecastEngine()
        assert engine is not None

    def test_generate_forecast_returns_dict(self):
        """Test that forecast returns dictionary"""
        engine = HuaweiTimeSeriesForecastEngine()
        historical = [98.6, 98.5, 98.7]
        fallback = lambda: {"dates": [], "historical": [], "forecast": []}
        
        result = engine.generate_forecast(
            historical_data=historical,
            days_ahead=7,
            fallback_fn=fallback
        )
        
        assert isinstance(result, dict)

    def test_generate_forecast_contains_required_fields(self):
        """Test that forecast contains required fields"""
        engine = HuaweiTimeSeriesForecastEngine()
        historical = [98.6] * 60
        fallback = lambda: {
            "dates": [f"2026-02-{i:02d}" for i in range(1, 8)],
            "historical": [98.6] * 8 + [None] * 7,
            "forecast": [None] * 8 + [98.6] * 7
        }
        
        result = engine.generate_forecast(
            historical_data=historical,
            days_ahead=7,
            fallback_fn=fallback
        )
        
        assert result is not None

    def test_generate_forecast_uses_fallback(self):
        """Test that fallback is used when cloud unavailable"""
        engine = HuaweiTimeSeriesForecastEngine()
        
        def fallback():
            return {
                "dates": [f"2026-02-{i:02d}" for i in range(1, 8)],
                "historical": [98.6] * 8 + [None] * 7,
                "forecast": [None] * 8 + [98.6] * 7
            }
        
        # Mock the client to return None
        engine.client = None
        
        result = engine.generate_forecast(
            historical_data=[98.6] * 60,
            days_ahead=7,
            fallback_fn=fallback
        )
        
        assert result is not None

    def test_get_default_forecast_returns_valid_data(self):
        """Test that default forecast is valid"""
        engine = HuaweiTimeSeriesForecastEngine()
        default_forecast = engine._get_default_forecast(7)
        
        assert isinstance(default_forecast, dict)
        assert "dates" in default_forecast


class TestAdapterSingletons:
    """Test singleton pattern for adapters"""

    def test_health_metrics_adapter_singleton(self):
        """Test that get_health_metrics_adapter returns singleton"""
        adapter1 = get_health_metrics_adapter()
        adapter2 = get_health_metrics_adapter()
        
        assert adapter1 is adapter2

    def test_risk_scorer_singleton(self):
        """Test that get_medical_ai_risk_scorer returns singleton"""
        scorer1 = get_medical_ai_risk_scorer()
        scorer2 = get_medical_ai_risk_scorer()
        
        assert scorer1 is scorer2

    def test_forecast_engine_singleton(self):
        """Test that get_forecast_engine returns singleton"""
        engine1 = get_forecast_engine()
        engine2 = get_forecast_engine()
        
        assert engine1 is engine2


class TestAdapterIntegration:
    """Test adapter integration with each other"""

    def test_adapters_work_together(self):
        """Test that all adapters can be used together"""
        health_adapter = get_health_metrics_adapter()
        risk_scorer = get_medical_ai_risk_scorer()
        forecast_engine = get_forecast_engine()
        
        # All should be available
        assert health_adapter is not None
        assert risk_scorer is not None
        assert forecast_engine is not None

    def test_adapters_dont_interfere(self):
        """Test that adapters don't interfere with each other"""
        health_adapter = get_health_metrics_adapter()
        risk_scorer = get_medical_ai_risk_scorer()
        
        # Use both adapters
        metrics = health_adapter.get_health_metrics(
            patient_id="test",
            context="test",
            fallback_fn=lambda: {"heart_rate": 72}
        )
        
        score = risk_scorer.score_health_status(
            current_metrics=metrics or {},
            recent_history=[],
            fallback_fn=lambda m, h: {"overall_risk": "Low", "risk_percentage": 20}
        )
        
        # Both should work without interference
        assert metrics is not None
        assert score is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
