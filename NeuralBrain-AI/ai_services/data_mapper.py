"""
Data mapper - Normalizes responses from Huawei APIs to expected schemas

Ensures all cloud responses match the exact data contracts required by the frontend.
Validates response structure and handles missing fields gracefully.
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class DataMapper:
    """Maps Huawei API responses to standard schemas"""
    
    @staticmethod
    def map_health_metrics(huawei_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Huawei health metrics response to standard schema
        
        Expected output:
        {
            "heart_rate": number,
            "temperature": number,
            "blood_pressure_sys": number,
            "blood_pressure_dia": number,
            "oxygen_saturation": number,
            "respiratory_rate": number,
            "glucose_level": number,
            "bmi": number,
            "activity_level": string,
            "confidence": float
        }
        """
        if not huawei_response:
            return None
        
        try:
            # Map fields, using defaults if missing
            result = {
                "heart_rate": huawei_response.get("heart_rate", 72),
                "temperature": huawei_response.get("temperature", 37.0),
                "blood_pressure_sys": huawei_response.get("blood_pressure_sys", 120),
                "blood_pressure_dia": huawei_response.get("blood_pressure_dia", 80),
                "oxygen_saturation": huawei_response.get("oxygen_saturation", 98),
                "respiratory_rate": huawei_response.get("respiratory_rate", 14),
                "glucose_level": huawei_response.get("glucose_level", 95),
                "bmi": huawei_response.get("bmi", 23.5),
                "activity_level": huawei_response.get("activity_level", "moderate"),
                "confidence": float(huawei_response.get("confidence", 0.9)),
                "timestamp": huawei_response.get("timestamp"),
            }
            
            DataMapper._validate_schema("health_metrics", result)
            return result
        
        except Exception as e:
            logger.error(f"Error mapping health metrics: {str(e)}")
            return None
    
    @staticmethod
    def map_risk_score(huawei_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Huawei risk score response to standard RiskScore schema
        
        Expected output:
        {
            "overall_risk": "Low" | "Medium" | "High",
            "risk_percentage": float (0-100),
            "risk_factors": [...],
            "trend_analysis": {...},
            "recommendations": [...],
            "confidence": float (0-1),
            "timestamp": ISO datetime
        }
        """
        if not huawei_response:
            return None
        
        try:
            # Normalize risk level capitalization
            overall_risk = huawei_response.get("overall_risk", "Medium")
            if isinstance(overall_risk, str):
                overall_risk = overall_risk.capitalize()
            
            result = {
                "overall_risk": overall_risk,
                "risk_percentage": float(huawei_response.get("risk_percentage", 50)),
                "risk_factors": huawei_response.get("risk_factors", []),
                "trend_analysis": huawei_response.get("trend_analysis", {}),
                "recommendations": huawei_response.get("recommendations", []),
                "confidence": float(huawei_response.get("confidence", 0.85)),
                "timestamp": huawei_response.get("timestamp"),
            }
            
            # Validate risk factors structure
            for factor in result.get("risk_factors", []):
                if not isinstance(factor, dict):
                    logger.warning(f"Invalid risk factor structure: {factor}")
            
            DataMapper._validate_schema("risk_score", result)
            return result
        
        except Exception as e:
            logger.error(f"Error mapping risk score: {str(e)}")
            return None
    
    @staticmethod
    def map_forecast(huawei_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Huawei forecast response to chart data schema
        
        Expected output:
        {
            "dates": ["2026-02-03", ...],
            "historical": [45, 48, ..., null, ...],
            "forecast": [null, ..., 65, 67, ...],
            "regions": [{"region": "...", "risk_score": 78, ...}]
        }
        """
        if not huawei_response:
            return None
        
        try:
            forecast_data = huawei_response.get("forecast", [])
            historical_data = huawei_response.get("historical_data", [])
            
            # Extract dates
            dates = []
            historical_values = []
            forecast_values = []
            
            # Historical dates (with values)
            for item in historical_data[:8]:  # Past + today
                dates.append(item.get("timestamp"))
                historical_values.append(item.get("value"))
            
            # Gap for separating historical from forecast
            for _ in range(7):
                historical_values.append(None)
            
            # Forecast dates and values
            for item in forecast_data[:7]:  # 7 days ahead
                dates.append(item.get("timestamp"))
                forecast_values.append(None)  # Nulls up to today
            
            # Add connector and forecast values
            forecast_values.extend([historical_data[-1].get("value")] if historical_data else [None])
            for item in forecast_data[:7]:
                forecast_values.append(item.get("point_forecast"))
            
            # Map regions
            regions = huawei_response.get("regions", [])
            if not regions:
                regions = [{
                    "region": "Global",
                    "risk_score": int(sum(v for v in historical_values if v) / max(1, len([v for v in historical_values if v]))),
                    "trend": "stable",
                    "status": "Medium Risk"
                }]
            
            result = {
                "dates": dates,
                "historical": historical_values,
                "forecast": forecast_values,
                "regions": regions
            }
            
            DataMapper._validate_schema("forecast", result)
            return result
        
        except Exception as e:
            logger.error(f"Error mapping forecast: {str(e)}")
            return None
    
    @staticmethod
    def _validate_schema(schema_name: str, data: Dict[str, Any]):
        """Validate that mapped data has required fields"""
        required_fields = {
            "health_metrics": ["heart_rate", "temperature", "blood_pressure_sys", 
                              "blood_pressure_dia", "oxygen_saturation", "respiratory_rate", "glucose_level"],
            "risk_score": ["overall_risk", "risk_percentage", "confidence"],
            "forecast": ["dates", "historical", "forecast"],
        }
        
        if schema_name in required_fields:
            missing = [f for f in required_fields[schema_name] if f not in data]
            if missing:
                logger.warning(f"Missing fields in {schema_name}: {missing}")
