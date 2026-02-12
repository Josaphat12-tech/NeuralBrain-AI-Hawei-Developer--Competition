"""
Health metrics inference adapter - Huawei ModelArts integration

Replaces dummy random health metrics with real inference from Huawei ModelArts.
Falls back to original random generator if cloud is unavailable.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ai_services.config import config
from ai_services.huawei_client import HuaweiAPIClient
from ai_services.data_mapper import DataMapper
from ai_services.fallback_manager import fallback_manager

logger = logging.getLogger(__name__)


class HuaweiHealthMetricsAdapter:
    """Adapter for health metrics inference via Huawei ModelArts"""
    
    def __init__(self):
        """Initialize adapter"""
        self.client = None
        if config.ENABLED:
            try:
                self.client = HuaweiAPIClient(
                    api_key=config.MODELARTS_API_KEY,
                    endpoint=config.MODELARTS_ENDPOINT,
                    timeout=config.HEALTH_METRICS_TIMEOUT
                )
                logger.info("✅ Health Metrics Inference Adapter initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Health Metrics Adapter: {str(e)}")
                self.client = None
        else:
            logger.info("ℹ️ Health Metrics Inference disabled (HUAWEI_CLOUD_ENABLED=false)")
            self.client = None
    
    def get_health_metrics(
        self,
        patient_id: str = "default",
        context: str = "daily_monitoring",
        fallback_fn=None
    ) -> Dict[str, Any]:
        """
        Get health metrics from Huawei ModelArts or fallback
        
        Args:
            patient_id: Patient identifier
            context: Context for inference (daily_monitoring, acute_assessment)
            fallback_fn: Fallback function if cloud unavailable
        
        Returns:
            Health metrics dictionary matching standard schema
        """
        # Try cloud first
        if self.client and config.ENABLED:
            cloud_result = self._call_modelarts_inference(patient_id, context)
            if cloud_result:
                mapped = DataMapper.map_health_metrics(cloud_result)
                if mapped:
                    logger.info(f"Health metrics retrieved from Huawei ModelArts for {patient_id}")
                    return mapped
        
        # Fall back to provided function
        if fallback_fn:
            logger.debug(f"Falling back to local function for health metrics")
            return fallback_fn()
        
        # Default fallback
        logger.warning("No fallback provided for health metrics, using minimal defaults")
        return self._get_default_metrics()
    
    def _call_modelarts_inference(
        self,
        patient_id: str,
        context: str
    ) -> Optional[Dict[str, Any]]:
        """
        Call Huawei ModelArts health metrics inference
        
        Args:
            patient_id: Patient identifier
            context: Inference context
        
        Returns:
            Response from ModelArts or None on failure
        """
        if not self.client:
            return None
        
        try:
            payload = {
                "patient_id": patient_id,
                "context": context,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "demographics": {
                    "age": 35,
                    "gender": "M",
                    "weight_kg": 75,
                    "height_cm": 180
                }
            }
            
            response = self.client.post(config.HEALTH_MODEL_ENDPOINT, payload)
            return response
        
        except Exception as e:
            logger.warning(f"ModelArts inference failed: {str(e)}")
            return None
    
    def _get_default_metrics(self) -> Dict[str, Any]:
        """Return default health metrics"""
        return {
            "heart_rate": 72,
            "temperature": 37.0,
            "blood_pressure_sys": 120,
            "blood_pressure_dia": 80,
            "oxygen_saturation": 98,
            "respiratory_rate": 14,
            "glucose_level": 95,
            "bmi": 23.5,
            "activity_level": "moderate",
            "confidence": 0.5,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def __del__(self):
        """Cleanup on destruction"""
        if self.client:
            self.client.close()


# Singleton instance
_health_adapter = None


def get_health_metrics_adapter() -> HuaweiHealthMetricsAdapter:
    """Get or create health metrics adapter singleton"""
    global _health_adapter
    if _health_adapter is None:
        _health_adapter = HuaweiHealthMetricsAdapter()
    return _health_adapter
