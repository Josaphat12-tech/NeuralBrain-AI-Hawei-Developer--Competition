"""
AI-Based Health Risk Scoring System
Simplified version for Python 3.14 compatibility (No Numpy/Sklearn)
Uses pure Python rule-based approach
"""

import logging
import math
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RiskScore:
    """Risk assessment result"""
    overall_risk: str  # 'Low', 'Medium', 'High'
    risk_percentage: float  # 0-100
    risk_factors: List[Dict]
    trend_analysis: Dict
    recommendations: List[str]
    confidence: float  # 0-1
    timestamp: str


class HealthTrendDetector:
    """Detects health trends from historical data using pure Python"""
    
    @staticmethod
    def detect_trend(values: List[float]) -> Tuple[str, float]:
        """
        Detect if metric is trending up, down, or stable
        Returns: (trend_direction, trend_strength_0_to_1)
        """
        if len(values) < 2:
            return "stable", 0.0
        
        # Simple slope calculation (last - first)
        diff = values[-1] - values[0]
        avg = sum(values) / len(values)
        
        if avg == 0:
            return "stable", 0.0
            
        rel_change = diff / avg
        
        if abs(rel_change) < 0.05:
            return "stable", 0.0
        elif rel_change > 0:
            strength = min(1.0, rel_change * 5)
            return "increasing", strength
        else:
            strength = min(1.0, abs(rel_change) * 5)
            return "decreasing", strength
    
    @staticmethod
    def calculate_volatility(values: List[float]) -> float:
        """Calculate metric volatility (coefficient of variation) using pure Python"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        if mean == 0:
            return 0.0
            
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)
        
        cv = std_dev / abs(mean)
        return min(1.0, cv)


class RuleBasedRiskAssessment:
    """Rule-based risk assessment using health guidelines"""
    
    # Clinical ranges (normal, warning, critical)
    HEALTH_RANGES = {
        'heart_rate': {
            'normal': (60, 100),
            'warning': (50, 120),
            'critical': (40, 140)
        },
        'temperature': {
            'normal': (36.5, 37.5),
            'warning': (35.5, 38.5),
            'critical': (35.0, 39.0)
        },
        'blood_pressure_sys': {
            'normal': (90, 120),
            'warning': (80, 140),
            'critical': (70, 180)
        },
        'blood_pressure_dia': {
            'normal': (60, 80),
            'warning': (50, 90),
            'critical': (40, 110)
        },
        'oxygen_saturation': {
            'normal': (95, 100),
            'warning': (90, 100),
            'critical': (85, 100)
        },
        'glucose_level': {
            'normal': (70, 100),
            'warning': (60, 140),
            'critical': (50, 200)
        },
        'respiratory_rate': {
            'normal': (12, 20),
            'warning': (10, 25),
            'critical': (8, 30)
        }
    }
    
    @staticmethod
    def assess_metric(metric_name: str, value: float) -> Tuple[str, float]:
        """
        Assess single metric against health guidelines
        Returns: (risk_level, risk_score_0_to_1)
        """
        if metric_name not in RuleBasedRiskAssessment.HEALTH_RANGES:
            return "unknown", 0.5
        
        ranges = RuleBasedRiskAssessment.HEALTH_RANGES[metric_name]
        
        # Check if in normal range
        if ranges['normal'][0] <= value <= ranges['normal'][1]:
            return "low", 0.1
        
        # Check if in warning range
        if ranges['warning'][0] <= value <= ranges['warning'][1]:
            return "medium", 0.5
        
        # Check if in critical range
        if ranges['critical'][0] <= value <= ranges['critical'][1]:
            return "high", 0.8
        
        # Out of all ranges - very high risk
        return "high", 0.95
    
    @staticmethod
    def assess_combination(metrics: Dict[str, float]) -> Tuple[str, float, List[Dict]]:
        """
        Assess combination of metrics
        Returns: (overall_risk, risk_score, risk_factors)
        """
        risk_factors = []
        risk_scores = []
        
        for metric_name, value in metrics.items():
            risk_level, risk_score = RuleBasedRiskAssessment.assess_metric(metric_name, value)
            
            if risk_level != "low":
                risk_factors.append({
                    'metric': metric_name,
                    'value': value,
                    'risk_level': risk_level,
                    'risk_score': risk_score
                })
            
            risk_scores.append(risk_score)
        
        # Calculate overall risk
        if not risk_scores:
            overall_risk = "low"
            overall_score = 0.1
        else:
            # Use average score
            overall_score = sum(risk_scores) / len(risk_scores)
            
            if overall_score < 0.3:
                overall_risk = "low"
            elif overall_score < 0.6:
                overall_risk = "medium"
            else:
                overall_risk = "high"
        
        return overall_risk, overall_score, risk_factors


class MLAnomalyDetector:
    """Mock ML detector for compatibility"""
    
    def __init__(self):
        self.is_trained = False
    
    def train(self, historical_data: List[Dict[str, float]]) -> bool:
        self.is_trained = True
        return True
    
    def detect_anomalies(self, recent_data: List[Dict[str, float]]) -> Tuple[float, List[int]]:
        return 0.0, []


class HealthRiskScorer:
    """Main risk scoring engine using pure Python"""
    
    def __init__(self):
        self.trend_detector = HealthTrendDetector()
        self.rule_assessor = RuleBasedRiskAssessment()
        self.ml_detector = MLAnomalyDetector()
    
    def train_on_history(self, health_records: List) -> bool:
        return True
    
    def score_health_status(
        self,
        current_metrics: Dict[str, float],
        recent_history: Optional[List[Dict[str, float]]] = None,
        all_history: Optional[List[Dict[str, float]]] = None
    ) -> RiskScore:
        try:
            timestamp = datetime.now().isoformat()
            recommendations = []
            trend_analysis = {}
            all_risk_factors = []
            
            # 1. RULE-BASED ASSESSMENT (60% weight)
            rule_risk, rule_score, rule_factors = self.rule_assessor.assess_combination(current_metrics)
            all_risk_factors.extend(rule_factors)
            rule_weight = 0.6
            
            # 2. TREND ANALYSIS (40% weight)
            trend_weight = 0.4
            trend_score = 0.1
            
            if recent_history and len(recent_history) >= 3:
                metric_trends = {}
                for metric_name in current_metrics.keys():
                    values = [m.get(metric_name, 0) for m in recent_history if metric_name in m]
                    if not values:
                         continue
                         
                    trend, strength = self.trend_detector.detect_trend(values)
                    metric_trends[metric_name] = {
                        'trend': trend,
                        'strength': strength
                    }
                    
                    # Detect concerning trends
                    if trend == "increasing" and metric_name in ['heart_rate', 'blood_pressure_sys', 'temperature']:
                        recommendations.append(f"⚠️ {metric_name.replace('_', ' ').title()} trending upward")
                        trend_score += strength * 0.15
                    
                    if trend == "decreasing" and metric_name in ['oxygen_saturation']:
                        recommendations.append(f"⚠️ {metric_name.replace('_', ' ').title()} trending downward")
                        trend_score += strength * 0.15
                
                trend_analysis = metric_trends
            
            # 5. COMBINED SCORING
            weighted_score = (
                rule_score * rule_weight +
                trend_score * trend_weight
            )
            
            # Determine overall risk
            if weighted_score < 0.25:
                overall_risk = "Low"
                confidence = 0.95
            elif weighted_score < 0.60:
                overall_risk = "Medium"
                confidence = 0.85
            else:
                overall_risk = "High"
                confidence = 0.90
            
            # Convert to percentage
            risk_percentage = min(100, weighted_score * 100)
            
            # Add general recommendations
            if overall_risk == "Low":
                recommendations.append("✅ Continue current health routine")
                recommendations.append("📈 Regular monitoring recommended")
            elif overall_risk == "Medium":
                recommendations.append("⚡ Consider lifestyle adjustments")
                recommendations.append("🏥 Schedule routine check-up")
            else:
                recommendations.append("🚨 Seek professional medical consultation")
                recommendations.append("📞 Contact healthcare provider")
            
            return RiskScore(
                overall_risk=overall_risk,
                risk_percentage=risk_percentage,
                risk_factors=all_risk_factors,
                trend_analysis=trend_analysis,
                recommendations=recommendations,
                confidence=confidence,
                timestamp=timestamp
            )
            
        except Exception as e:
            logger.error(f"Error in health risk scoring: {e}")
            return RiskScore(
                overall_risk="Unknown",
                risk_percentage=50.0,
                risk_factors=[],
                trend_analysis={},
                recommendations=["Error during assessment"],
                confidence=0.0,
                timestamp=datetime.now().isoformat()
            )
    
    def get_risk_summary(self, risk_score: RiskScore) -> Dict:
        """Convert RiskScore to dictionary for JSON response"""
        return {
            'overall_risk': risk_score.overall_risk,
            'risk_percentage': round(risk_score.risk_percentage, 2),
            'risk_factors': risk_score.risk_factors,
            'trend_analysis': risk_score.trend_analysis,
            'recommendations': risk_score.recommendations,
            'confidence': round(risk_score.confidence, 2),
            'timestamp': risk_score.timestamp
        }


# Global risk scorer instance
_risk_scorer = None


def get_risk_scorer() -> HealthRiskScorer:
    """Get or create global risk scorer instance"""
    global _risk_scorer
    if _risk_scorer is None:
        _risk_scorer = HealthRiskScorer()
    return _risk_scorer


def calculate_health_risk(
    health_records: List,
    current_index: int = -1
) -> Optional[Dict]:
    """
    Calculate health risk for a specific record
    """
    if not health_records:
        return None
    
    if current_index == -1:
        current_index = len(health_records) - 1
    
    current_record = health_records[current_index]
    current_metrics_obj = current_record.metrics or {}
    
    # Get recent history (last 20 records)
    start_idx = max(0, current_index - 20)
    recent_history = []
    
    for idx in range(start_idx, current_index + 1):
        record = health_records[idx]
        metrics = record.metrics or {}
        
        recent_history.append({
            'heart_rate': metrics.get('heart_rate', 75),
            'temperature': metrics.get('temperature', 37.0),
            'blood_pressure_sys': metrics.get('blood_pressure_systolic', 120),
            'blood_pressure_dia': metrics.get('blood_pressure_diastolic', 80),
            'oxygen_saturation': metrics.get('oxygen_saturation', 98),
            'glucose_level': metrics.get('glucose_level', 100),
            'respiratory_rate': metrics.get('respiratory_rate', 16)
        })
    
    # Current metrics
    current_metrics = {
        'heart_rate': current_metrics_obj.get('heart_rate', 75),
        'temperature': current_metrics_obj.get('temperature', 37.0),
        'blood_pressure_sys': current_metrics_obj.get('blood_pressure_systolic', 120),
        'blood_pressure_dia': current_metrics_obj.get('blood_pressure_diastolic', 80),
        'oxygen_saturation': current_metrics_obj.get('oxygen_saturation', 98),
        'glucose_level': current_metrics_obj.get('glucose_level', 100),
        'respiratory_rate': current_metrics_obj.get('respiratory_rate', 16)
    }
    
    # Get scorer and train if needed
    scorer = get_risk_scorer()
    
    # Generate risk score
    risk_score = scorer.score_health_status(
        current_metrics=current_metrics,
        recent_history=recent_history,
        all_history=recent_history
    )
    
    return scorer.get_risk_summary(risk_score)
