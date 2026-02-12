"""
Time-series forecasting engine - Huawei TimeSeries Forecast API integration

Replaces random walk forecasting with real time-series prediction.
Falls back to original random generation if cloud is unavailable.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ai_services.config import config
from ai_services.huawei_client import HuaweiAPIClient
from ai_services.data_mapper import DataMapper
from ai_services.fallback_manager import fallback_manager

logger = logging.getLogger(__name__)


class HuaweiTimeSeriesForecastEngine:
    """Time-series forecasting using Huawei TimeSeries Forecast API"""
    
    def __init__(self):
        """Initialize forecast engine"""
        self.client = None
        if config.ENABLED:
            try:
                self.client = HuaweiAPIClient(
                    api_key=config.MODELARTS_API_KEY,
                    endpoint=config.TIMESERIES_ENDPOINT,
                    timeout=config.FORECAST_TIMEOUT
                )
                logger.info("✅ Time-Series Forecast Engine initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Time-Series Forecast Engine: {str(e)}")
                self.client = None
        else:
            logger.info("ℹ️ Time-Series Forecast Engine disabled (HUAWEI_CLOUD_ENABLED=false)")
            self.client = None
    
    def generate_forecast(
        self,
        historical_data: Optional[List[Dict[str, Any]]] = None,
        days_ahead: int = 7,
        fallback_fn=None
    ) -> Dict[str, Any]:
        """
        Generate forecast using Huawei TimeSeries API
        
        Args:
            historical_data: Historical time-series data
            days_ahead: Number of days to forecast
            fallback_fn: Fallback function if cloud unavailable
        
        Returns:
            Chart data dictionary with dates, historical, forecast, regions
        """
        # Check if Huawei Cloud is disabled in config
        if not config.ENABLED:
            logger.debug("Huawei Cloud disabled - using fallback forecast")
            if fallback_fn:
                return fallback_fn()
            return self._get_default_forecast(days_ahead)
        
        # Try cloud if enabled
        if self.client and historical_data and len(historical_data) >= 7:
            cloud_result = self._call_timeseries_forecast_api(
                historical_data,
                days_ahead
            )
            if cloud_result:
                mapped = DataMapper.map_forecast(cloud_result)
                if mapped:
                    logger.info("✅ Forecast retrieved from Huawei TimeSeries API")
                    return mapped
        
        # Fall back to provided function
        if fallback_fn:
            logger.debug("Falling back to local forecast generation")
            return fallback_fn()
        
        # Default fallback - simple random walk
        logger.debug("Using default fallback forecast")
        return self._get_default_forecast(days_ahead)
    
    def _call_timeseries_forecast_api(
        self,
        historical_data: List[Dict[str, Any]],
        days_ahead: int
    ) -> Optional[Dict[str, Any]]:
        """
        Call Huawei TimeSeries Forecast API
        
        Args:
            historical_data: Historical data points
            days_ahead: Forecast horizon
        
        Returns:
            Forecast response or None on failure
        """
        if not self.client:
            return None
        
        try:
            # Prepare time series for API
            time_series = []
            for item in historical_data[-60:]:  # Last 60 days
                time_series.append({
                    "timestamp": item.get("timestamp", ""),
                    "value": item.get("risk_score", item.get("value", 50))
                })
            
            payload = {
                "time_series": time_series,
                "forecast_horizon": days_ahead,
                "confidence_level": 0.95,
                "include_anomalies": True,
                "seasonality": "weekly"
            }
            
            response = self.client.post(config.FORECAST_API_ENDPOINT, payload)
            return response
        
        except Exception as e:
            logger.warning(f"TimeSeries forecast failed: {str(e)}")
            return None
    
    def _get_default_forecast(self, days_ahead: int = 7) -> Dict[str, Any]:
        """
        Generate default forecast using simple random walk
        
        Used as fallback when cloud is unavailable
        """
        dates = []
        historical = []
        forecast = []
        
        # Generate dates for past 8 days + future
        today = datetime.now()
        for i in range(-7, days_ahead + 1):
            date = today + timedelta(days=i)
            dates.append(date.strftime("%Y-%m-%d"))
        
        # Generate historical values (8 points)
        current_value = 45
        for i in range(8):
            historical.append(int(current_value))
            current_value += 2
        
        # Add nulls for gap
        for _ in range(7):
            historical.append(None)
        
        # Generate forecast values
        for i in range(8):
            forecast.append(None)
        
        # Add connector and forecast points
        forecast.append(int(current_value))
        for i in range(7):
            forecast.append(int(current_value + (i + 1) * 1.5))
        
        return {
            "dates": dates,
            "historical": historical,
            "forecast": forecast,
            "regions": [
                {
                    "region": "Southeast Asia",
                    "risk_score": 55,
                    "trend": "Stable",
                    "status": "Medium Risk"
                },
                {
                    "region": "East Asia",
                    "risk_score": 48,
                    "trend": "Decreasing",
                    "status": "Low Risk"
                },
                {
                    "region": "South Asia",
                    "risk_score": 62,
                    "trend": "Increasing",
                    "status": "High Risk"
                }
            ]
        }
    
    def __del__(self):
        """Cleanup on destruction"""
        if self.client:
            self.client.close()


# Singleton instance
_forecast_engine = None


def get_forecast_engine() -> HuaweiTimeSeriesForecastEngine:
    """Get or create forecast engine singleton"""
    global _forecast_engine
    if _forecast_engine is None:
        _forecast_engine = HuaweiTimeSeriesForecastEngine()
    return _forecast_engine
