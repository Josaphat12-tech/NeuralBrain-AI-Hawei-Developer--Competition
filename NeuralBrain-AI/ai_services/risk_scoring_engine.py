"""
Medical AI risk scoring engine - Huawei ModelArts integration

Replaces rule-based risk scoring with real medical AI model inference.
Falls back to rule-based scoring if cloud is unavailable.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ai_services.config import config
from ai_services.huawei_client import HuaweiAPIClient
from ai_services.data_mapper import DataMapper
from ai_services.fallback_manager import fallback_manager

logger = logging.getLogger(__name__)


class HuaweiMedicalAIRiskScorer:
    """Medical AI risk scorer using Huawei ModelArts"""
    
    def __init__(self):
        """Initialize risk scorer"""
        self.client = None
        if config.ENABLED:
            try:
                self.client = HuaweiAPIClient(
                    api_key=config.MODELARTS_API_KEY,
                    endpoint=config.MODELARTS_ENDPOINT,
                    timeout=config.RISK_SCORING_TIMEOUT
                )
                logger.info("✅ Medical AI Risk Scorer initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Risk Scorer: {str(e)}")
                self.client = None
        else:
            logger.info("ℹ️ Medical AI Risk Scoring disabled (HUAWEI_CLOUD_ENABLED=false)")
            self.client = None
    
    def score_health_status(
        self,
        current_metrics: Dict[str, Any],
        recent_history: Optional[List[Dict[str, Any]]] = None,
        fallback_fn=None
    ) -> Dict[str, Any]:
        """
        Score health status using Huawei Medical AI
        
        Args:
            current_metrics: Current health metrics
            recent_history: Recent historical metrics (last 7 days)
            fallback_fn: Fallback function if cloud unavailable
        
        Returns:
            Risk score dictionary matching standard RiskScore schema
        """
        # Try cloud first
        if self.client and config.ENABLED:
            cloud_result = self._call_medical_ai_inference(
                current_metrics,
                recent_history or []
            )
            if cloud_result:
                mapped = DataMapper.map_risk_score(cloud_result)
                if mapped:
                    logger.info("Risk score retrieved from Huawei Medical AI")
                    return mapped
        
        # Fall back to provided function
        if fallback_fn:
            logger.debug("Falling back to local scoring for risk assessment")
            return fallback_fn(current_metrics, recent_history or [])
        
        # Default fallback - basic rule-based scoring
        logger.warning("No fallback provided for risk scoring, using default")
        return self._get_default_risk_score(current_metrics)
    
    def _call_medical_ai_inference(
        self,
        current_metrics: Dict[str, Any],
        recent_history: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Call Huawei Medical AI risk assessment model
        
        Args:
            current_metrics: Current health metrics
            recent_history: Historical metrics
        
        Returns:
            Risk score response or None on failure
        """
        if not self.client:
            return None
        
        try:
            payload = {
                "patient_id": "default",
                "current_metrics": {
                    "heart_rate": current_metrics.get("heart_rate", 72),
                    "temperature": current_metrics.get("temperature", 37.0),
                    "blood_pressure_sys": current_metrics.get("blood_pressure_sys", 120),
                    "blood_pressure_dia": current_metrics.get("blood_pressure_dia", 80),
                    "oxygen_saturation": current_metrics.get("oxygen_saturation", 98),
                    "respiratory_rate": current_metrics.get("respiratory_rate", 14),
                    "glucose_level": current_metrics.get("glucose_level", 95),
                },
                "recent_history": recent_history[-7:] if recent_history else [],
                "medical_context": {
                    "age": 35,
                    "conditions": [],
                    "medications": []
                }
            }
            
            response = self.client.post(config.RISK_MODEL_ENDPOINT, payload)
            return response
        
        except Exception as e:
            logger.warning(f"Medical AI inference failed: {str(e)}")
            return None
    
    def _get_default_risk_score(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate default risk score using simple heuristics
        
        Used as fallback when cloud is unavailable
        """
        heart_rate = metrics.get("heart_rate", 72)
        bp_sys = metrics.get("blood_pressure_sys", 120)
        glucose = metrics.get("glucose_level", 95)
        
        # Simple risk calculation
        risk_score = 0
        factors = []
        
        if heart_rate < 60 or heart_rate > 100:
            risk_score += 20
            factors.append({
                "metric": "heart_rate",
                "value": heart_rate,
                "risk_level": "high" if heart_rate < 50 or heart_rate > 110 else "medium",
                "risk_score": 0.7
            })
        
        if bp_sys > 140:
            risk_score += 25
            factors.append({
                "metric": "blood_pressure_sys",
                "value": bp_sys,
                "risk_level": "high",
                "risk_score": 0.8
            })
        
        if glucose < 70 or glucose > 125:
            risk_score += 15
            factors.append({
                "metric": "glucose_level",
                "value": glucose,
                "risk_level": "medium",
                "risk_score": 0.6
            })
        
        # Determine overall risk level
        if risk_score > 50:
            overall_risk = "High"
        elif risk_score > 25:
            overall_risk = "Medium"
        else:
            overall_risk = "Low"
        
        return {
            "overall_risk": overall_risk,
            "risk_percentage": min(100, risk_score),
            "risk_factors": factors,
            "trend_analysis": {},
            "recommendations": [
                "Continue regular monitoring",
                "Maintain healthy lifestyle"
            ],
            "confidence": 0.85,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def __del__(self):
        """Cleanup on destruction"""
        if self.client:
            self.client.close()


# Singleton instance
_risk_scorer = None


def get_medical_ai_risk_scorer() -> HuaweiMedicalAIRiskScorer:
    """Get or create risk scorer singleton"""
    global _risk_scorer
    if _risk_scorer is None:
        _risk_scorer = HuaweiMedicalAIRiskScorer()
    return _risk_scorer
