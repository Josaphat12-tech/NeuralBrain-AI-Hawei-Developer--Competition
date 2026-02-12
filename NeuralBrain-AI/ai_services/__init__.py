"""
AI Services Module - Huawei Cloud Integration Layer

This module provides adapters for replacing dummy data sources with real Huawei Cloud AI services.
All services include graceful fallback to original implementations if cloud is unavailable.

Services:
- Inference Adapter: Health metrics inference via ModelArts
- Risk Scoring Engine: Medical AI risk assessment via ModelArts
- Forecast Engine: Time-series forecasting via TimeSeries API
"""

from ai_services.inference_adapter import HuaweiHealthMetricsAdapter
from ai_services.risk_scoring_engine import HuaweiMedicalAIRiskScorer
from ai_services.forecast_engine import HuaweiTimeSeriesForecastEngine
from ai_services.config import AIServiceConfig

__version__ = "1.0.0"
__all__ = [
    "HuaweiHealthMetricsAdapter",
    "HuaweiMedicalAIRiskScorer",
    "HuaweiTimeSeriesForecastEngine",
    "AIServiceConfig",
]
