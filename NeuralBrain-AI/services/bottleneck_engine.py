"""
Bottleneck Forecasting Engine - Output Normalization & Consolidation

Normalizes outputs from any active AI provider into authoritative dataset.
Ensures consistent schema for all frontend components regardless of provider.

Single Output Source of Truth for all forecasts.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ForecastData:
    """Standardized forecast data structure"""
    region: str
    actual_cases: int
    actual_deaths: int
    actual_recovered: int
    forecasted_cases: List[Dict[str, Any]]  # [{"day": 1, "value": int}]
    forecasted_deaths: List[Dict[str, Any]]
    confidence_score: float  # 0.0-1.0
    risk_level: str  # RED, YELLOW, GREEN
    risk_score: float  # 0-100
    outbreak_probability: float  # 0.0-1.0
    trend: str  # increasing, decreasing, stable
    timestamp: str  # ISO8601
    provider: str  # openai, gemini, groq, etc
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class BottleneckForecastingEngine:
    """
    Normalizes AI provider outputs into authoritative forecast dataset.
    
    Acts as single bottleneck for all forecast operations - ensures:
    - Consistent schema
    - Numerical validation
    - Confidence calculation
    - Risk level assignment
    - Frontend data consistency
    """
    
    def __init__(self):
        """Initialize bottleneck engine"""
        self._forecasts_cache = {}  # region -> ForecastData
        self._last_update = None
        self._provider = None
        
        logger.info("🎯 Bottleneck Forecasting Engine initialized")
    
    def normalize_forecast(
        self,
        provider_output: Dict[str, Any],
        provider_name: str,
        actual_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> ForecastData:
        """
        Normalize provider output to standard forecast schema
        
        Args:
            provider_output: Raw output from AI provider
            provider_name: Name of provider (openai, gemini, etc)
            actual_data: Current actual cases/deaths data
            historical_data: Historical data for trend analysis
            
        Returns:
            ForecastData: Normalized forecast
        """
        try:
            # Extract numerical forecasts
            forecasted_cases = self._extract_cases_forecast(provider_output)
            forecasted_deaths = self._extract_deaths_forecast(provider_output)
            
            # Validate forecasts
            self._validate_forecasts(forecasted_cases, forecasted_deaths, actual_data)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(
                forecasted_cases,
                actual_data,
                historical_data,
                provider_name
            )
            
            # Determine risk level and score
            risk_level, risk_score = self._assess_risk(
                forecasted_cases,
                actual_data,
                historical_data
            )
            
            # Calculate outbreak probability
            outbreak_prob = self._calculate_outbreak_probability(
                forecasted_cases,
                actual_data,
                historical_data
            )
            
            # Determine trend
            trend = self._determine_trend(
                forecasted_cases,
                actual_data,
                historical_data
            )
            
            # Build standardized forecast
            region = actual_data.get('country', 'Global')
            
            forecast = ForecastData(
                region=region,
                actual_cases=actual_data.get('cases', 0),
                actual_deaths=actual_data.get('deaths', 0),
                actual_recovered=actual_data.get('recovered', 0),
                forecasted_cases=forecasted_cases,
                forecasted_deaths=forecasted_deaths,
                confidence_score=confidence,
                risk_level=risk_level,
                risk_score=risk_score,
                outbreak_probability=outbreak_prob,
                trend=trend,
                timestamp=datetime.utcnow().isoformat(),
                provider=provider_name
            )
            
            logger.info(f"✅ Normalized forecast for {region}: {risk_level} ({risk_score:.1f})")
            return forecast
            
        except Exception as e:
            logger.error(f"❌ Forecast normalization failed: {str(e)}")
            raise
    
    def _extract_cases_forecast(self, provider_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract case forecast from provider output"""
        try:
            # Try common field names
            if 'forecasted_cases' in provider_output:
                return provider_output['forecasted_cases']
            elif 'predicted_cases' in provider_output:
                return provider_output['predicted_cases']
            elif 'forecast' in provider_output and isinstance(provider_output['forecast'], list):
                return provider_output['forecast']
            
            # If AI response is JSON string, parse it
            if isinstance(provider_output, str):
                data = json.loads(provider_output)
                return data.get('forecasted_cases', [])
            
            logger.warning("⚠️ Could not extract cases forecast, using empty list")
            return []
            
        except Exception as e:
            logger.error(f"❌ Cases extraction failed: {str(e)}")
            return []
    
    def _extract_deaths_forecast(self, provider_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract deaths forecast from provider output"""
        try:
            if 'forecasted_deaths' in provider_output:
                return provider_output['forecasted_deaths']
            elif 'predicted_deaths' in provider_output:
                return provider_output['predicted_deaths']
            elif 'deaths_forecast' in provider_output:
                return provider_output['deaths_forecast']
            
            # Estimate from cases if not available
            logger.info("ℹ️ Deaths forecast not provided, estimating from cases")
            return []
            
        except Exception as e:
            logger.error(f"❌ Deaths extraction failed: {str(e)}")
            return []
    
    def _validate_forecasts(
        self,
        forecasted_cases: List[Dict[str, Any]],
        forecasted_deaths: List[Dict[str, Any]],
        actual_data: Dict[str, Any]
    ) -> None:
        """Validate forecast values are within reasonable ranges"""
        actual_cases = actual_data.get('cases', 0)
        
        for forecast in forecasted_cases:
            value = forecast.get('value', 0)
            
            # Check for invalid values
            if value < 0:
                logger.warning(f"⚠️ Negative forecast value: {value}")
                forecast['value'] = 0
            
            # Check for unrealistic values
            if actual_cases > 0:
                ratio = value / actual_cases
                if ratio > 10:
                    logger.warning(f"⚠️ Forecast {ratio}x higher than current: {value} vs {actual_cases}")
    
    def _calculate_confidence(
        self,
        forecasted_cases: List[Dict[str, Any]],
        actual_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
        provider_name: str
    ) -> float:
        """Calculate confidence score (0.0-1.0)"""
        try:
            confidence = 0.85  # Base confidence
            
            # Provider-specific adjustments
            if provider_name == 'openai':
                confidence = 0.90  # Higher confidence for OpenAI
            elif provider_name == 'gemini':
                confidence = 0.85
            elif provider_name == 'groq':
                confidence = 0.80
            
            # Adjust based on data volatility
            if historical_data and len(historical_data) > 7:
                volatility = self._calculate_volatility(historical_data)
                if volatility > 0.5:  # High volatility
                    confidence *= 0.8
            
            # Clamp between 0.5 and 0.98
            return max(0.5, min(0.98, confidence))
            
        except Exception as e:
            logger.error(f"❌ Confidence calculation failed: {str(e)}")
            return 0.75
    
    def _calculate_volatility(self, historical_data: List[Dict[str, Any]]) -> float:
        """Calculate historical data volatility"""
        try:
            cases = [d.get('cases', 0) for d in historical_data[-14:]]
            if not cases or len(cases) < 2:
                return 0.0
            
            # Calculate day-over-day percentage changes
            changes = []
            for i in range(1, len(cases)):
                if cases[i-1] > 0:
                    pct_change = abs((cases[i] - cases[i-1]) / cases[i-1])
                    changes.append(pct_change)
            
            if not changes:
                return 0.0
            
            return sum(changes) / len(changes)
            
        except Exception as e:
            logger.warning(f"⚠️ Volatility calculation failed: {str(e)}")
            return 0.0
    
    def _assess_risk(
        self,
        forecasted_cases: List[Dict[str, Any]],
        actual_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> Tuple[str, float]:
        """
        Assess risk level and score
        
        Returns:
            Tuple of (risk_level: str, risk_score: float)
        """
        try:
            actual_cases = actual_data.get('cases', 0)
            
            # Get forecast for day 7 if available
            day7_cases = forecasted_cases[-1]['value'] if forecasted_cases else actual_cases
            
            # Calculate growth rate
            if actual_cases > 0:
                growth_rate = (day7_cases - actual_cases) / actual_cases
            else:
                growth_rate = 0
            
            # Calculate growth per day
            daily_growth = growth_rate / 7 if growth_rate != 0 else 0
            
            # Assign risk level based on growth
            if daily_growth > 0.05:  # 5% daily growth
                risk_level = "RED"
                risk_score = 85.0 + (daily_growth * 100)
            elif daily_growth > 0.01:  # 1% daily growth
                risk_level = "YELLOW"
                risk_score = 55.0 + (daily_growth * 1000)
            else:
                risk_level = "GREEN"
                risk_score = min(50.0, 10 + (daily_growth * 1000))
            
            # Clamp risk score 0-100
            risk_score = max(0, min(100, risk_score))
            
            return risk_level, risk_score
            
        except Exception as e:
            logger.error(f"❌ Risk assessment failed: {str(e)}")
            return "GREEN", 25.0
    
    def _calculate_outbreak_probability(
        self,
        forecasted_cases: List[Dict[str, Any]],
        actual_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> float:
        """Calculate outbreak probability (0.0-1.0)"""
        try:
            actual_cases = actual_data.get('cases', 0)
            day7_cases = forecasted_cases[-1]['value'] if forecasted_cases else actual_cases
            
            if actual_cases == 0:
                return 0.0
            
            growth_rate = (day7_cases - actual_cases) / actual_cases
            
            # Convert growth rate to probability
            if growth_rate > 0.3:  # >30% growth
                return 0.95
            elif growth_rate > 0.1:
                return 0.70
            elif growth_rate > 0:
                return 0.40
            else:
                return 0.10
            
        except Exception as e:
            logger.error(f"❌ Outbreak probability calculation failed: {str(e)}")
            return 0.5
    
    def _determine_trend(
        self,
        forecasted_cases: List[Dict[str, Any]],
        actual_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> str:
        """Determine trend (increasing, decreasing, stable)"""
        try:
            actual_cases = actual_data.get('cases', 0)
            day7_cases = forecasted_cases[-1]['value'] if forecasted_cases else actual_cases
            
            if day7_cases > actual_cases * 1.05:
                return "increasing"
            elif day7_cases < actual_cases * 0.95:
                return "decreasing"
            else:
                return "stable"
            
        except Exception as e:
            logger.warning(f"⚠️ Trend determination failed: {str(e)}")
            return "stable"
    
    def cache_forecast(self, region: str, forecast: ForecastData) -> None:
        """Cache forecast for quick retrieval (deep copy)"""
        import copy
        self._forecasts_cache[region] = copy.deepcopy(forecast)
        self._last_update = datetime.utcnow()
        self._provider = forecast.provider
    
    def get_cached_forecast(self, region: str) -> Optional[ForecastData]:
        """Get cached forecast for region"""
        return self._forecasts_cache.get(region)
    
    def get_all_cached_forecasts(self) -> Dict[str, ForecastData]:
        """Get all cached forecasts"""
        return self._forecasts_cache.copy()
    
    def clear_cache(self) -> None:
        """Clear all cached forecasts"""
        self._forecasts_cache.clear()
        logger.info("✅ Forecast cache cleared")


# Global singleton instance
_bottleneck_instance = None


def get_bottleneck_engine() -> BottleneckForecastingEngine:
    """Get or create singleton instance"""
    global _bottleneck_instance
    if _bottleneck_instance is None:
        _bottleneck_instance = BottleneckForecastingEngine()
    return _bottleneck_instance
