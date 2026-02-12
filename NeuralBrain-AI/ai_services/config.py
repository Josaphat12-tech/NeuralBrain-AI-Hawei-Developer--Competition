"""
Configuration management for AI services

Loads Huawei Cloud credentials and API endpoints from environment variables.
Provides sensible defaults for development and testing.
"""

import os
from dataclasses import dataclass, field


@dataclass
class AIServiceConfig:
    """Configuration for AI services integration with Huawei Cloud"""
    
    # Feature flags
    ENABLED: bool = field(default_factory=lambda: os.getenv("HUAWEI_CLOUD_ENABLED", "true").lower() == "true")
    FALLBACK_ENABLED: bool = True  # Always fallback on failure
    CACHE_ENABLED: bool = field(default_factory=lambda: os.getenv("AI_SERVICE_CACHE_ENABLED", "true").lower() == "true")
    
    # Timeouts (seconds)
    TIMEOUT_SECONDS: int = field(default_factory=lambda: int(os.getenv("AI_SERVICE_TIMEOUT_SECONDS", "5")))
    HEALTH_METRICS_TIMEOUT: int = 3
    RISK_SCORING_TIMEOUT: int = 2
    FORECAST_TIMEOUT: int = 3
    
    # Cache settings (seconds)
    CACHE_TTL_SECONDS: int = field(default_factory=lambda: int(os.getenv("AI_SERVICE_CACHE_TTL_SECONDS", "3600")))
    
    # ModelArts Configuration
    MODELARTS_ENDPOINT: str = field(default_factory=lambda: os.getenv(
        "HUAWEI_MODELARTS_ENDPOINT", 
        "https://modelarts.cn-north-4.huaweicloud.com"
    ))
    MODELARTS_PROJECT_ID: str = field(default_factory=lambda: os.getenv("HUAWEI_MODELARTS_PROJECT_ID", ""))
    MODELARTS_API_KEY: str = field(default_factory=lambda: os.getenv("HUAWEI_API_KEY", ""))
    
    # Health Metrics Model
    HEALTH_MODEL_ID: str = field(default_factory=lambda: os.getenv(
        "HUAWEI_HEALTH_MODEL_ID",
        "health-inference-v1"
    ))
    HEALTH_MODEL_ENDPOINT: str = field(default_factory=lambda: os.getenv(
        "HUAWEI_HEALTH_MODEL_ENDPOINT",
        "/v1/infer/health-metrics"
    ))
    
    # Risk Scoring Model
    RISK_MODEL_ID: str = field(default_factory=lambda: os.getenv(
        "HUAWEI_RISK_MODEL_ID",
        "medical-risk-ai-v2"
    ))
    RISK_MODEL_ENDPOINT: str = field(default_factory=lambda: os.getenv(
        "HUAWEI_RISK_MODEL_ENDPOINT",
        "/v1/infer/medical-risk"
    ))
    
    # TimeSeries Forecast Configuration
    TIMESERIES_ENDPOINT: str = field(default_factory=lambda: os.getenv(
        "HUAWEI_TIMESERIES_ENDPOINT",
        "https://timeseries.cn-north-4.huaweicloud.com"
    ))
    FORECAST_API_ENDPOINT: str = field(default_factory=lambda: os.getenv(
        "HUAWEI_FORECAST_API_ENDPOINT",
        "/v1/forecast/health-risk"
    ))
    FORECAST_MODEL_ID: str = field(default_factory=lambda: os.getenv(
        "HUAWEI_FORECAST_MODEL_ID",
        "forecast-v1"
    ))
    
    # Logging
    DEBUG: bool = field(default_factory=lambda: os.getenv("AI_SERVICE_DEBUG", "false").lower() == "true")

    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        return cls()

    def is_available(self) -> bool:
        """Check if cloud services are configured and enabled"""
        return self.ENABLED and bool(self.MODELARTS_API_KEY)

    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.ENABLED and not self.MODELARTS_API_KEY:
            import logging
            logging.warning(
                "AI Services enabled but HUAWEI_API_KEY not set. "
                "Will use fallback implementations."
            )


# Global config instance
config = AIServiceConfig.from_env()
