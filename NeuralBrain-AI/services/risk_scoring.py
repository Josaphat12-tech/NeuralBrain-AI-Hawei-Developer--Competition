"""
AI-Based Health Risk Scoring System
Uses scikit-learn with hybrid rule-based + ML approach
No paid APIs - completely local and free
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.decomposition import PCA
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
    """Detects health trends from historical data"""
    
    @staticmethod
    def detect_trend(values: List[float]) -> Tuple[str, float]:
        """
        Detect if metric is trending up, down, or stable
        Returns: (trend_direction, trend_strength_0_to_1)
        """
        if len(values) < 2:
            return "stable", 0.0
        
        values = np.array(values, dtype=float)
        
        # Calculate trend using linear regression
        x = np.arange(len(values))
        coefficients = np.polyfit(x, values, 1)
        slope = coefficients[0]
        
        # Calculate standard deviation
        std_dev = np.std(values)
        
        if std_dev == 0:
            return "stable", 0.0
        
        # Normalize slope by standard deviation
        normalized_slope = slope / std_dev
        
        # Determine trend direction and strength
        if abs(normalized_slope) < 0.05:
            trend = "stable"
            strength = 0.0
        elif normalized_slope > 0.15:
            trend = "increasing"
            strength = min(1.0, abs(normalized_slope) / 0.5)
        elif normalized_slope < -0.15:
            trend = "decreasing"
            strength = min(1.0, abs(normalized_slope) / 0.5)
        else:
            trend = "slightly_" + ("increasing" if normalized_slope > 0 else "decreasing")
            strength = abs(normalized_slope) / 0.15
        
        return trend, min(1.0, strength)
    
    @staticmethod
    def calculate_volatility(values: List[float]) -> float:
        """Calculate metric volatility (0-1 scale)"""
        if len(values) < 2:
            return 0.0
        
        values = np.array(values, dtype=float)
        mean = np.mean(values)
        
        if mean == 0:
            return 0.0
        
        # Coefficient of variation
        cv = np.std(values) / abs(mean)
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
            # Use 75th percentile to avoid single outliers
            overall_score = np.percentile(risk_scores, 75)
            
            if overall_score < 0.3:
                overall_risk = "low"
            elif overall_score < 0.6:
                overall_risk = "medium"
            else:
                overall_risk = "high"
        
        return overall_risk, overall_score, risk_factors


class MLAnomalyDetector:
    """Machine learning-based anomaly detection using Isolation Forest"""
    
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def train(self, historical_data: List[Dict[str, float]]) -> bool:
        """
        Train anomaly detector on historical data
        Args: List of metric dictionaries
        Returns: True if training successful
        """
        if not historical_data or len(historical_data) < 10:
            logger.warning("Insufficient data for ML training")
            return False
        
        try:
            # Convert to feature matrix
            features = []
            for record in historical_data:
                feature_vector = [
                    record.get('heart_rate', 0),
                    record.get('temperature', 0),
                    record.get('blood_pressure_sys', 0),
                    record.get('blood_pressure_dia', 0),
                    record.get('oxygen_saturation', 0),
                    record.get('glucose_level', 0),
                    record.get('respiratory_rate', 0)
                ]
                features.append(feature_vector)
            
            features = np.array(features)
            
            # Standardize features
            features_scaled = self.scaler.fit_transform(features)
            
            # Train model
            self.model.fit(features_scaled)
            self.is_trained = True
            
            logger.info("✓ ML anomaly detector trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error training anomaly detector: {e}")
            return False
    
    def detect_anomalies(self, recent_data: List[Dict[str, float]]) -> Tuple[float, List[int]]:
        """
        Detect anomalies in recent data
        Returns: (anomaly_score_0_to_1, anomaly_indices)
        """
        if not self.is_trained or not recent_data:
            return 0.0, []
        
        try:
            # Convert to feature matrix
            features = []
            for record in recent_data:
                feature_vector = [
                    record.get('heart_rate', 0),
                    record.get('temperature', 0),
                    record.get('blood_pressure_sys', 0),
                    record.get('blood_pressure_dia', 0),
                    record.get('oxygen_saturation', 0),
                    record.get('glucose_level', 0),
                    record.get('respiratory_rate', 0)
                ]
                features.append(feature_vector)
            
            features = np.array(features)
            features_scaled = self.scaler.transform(features)
            
            # Get predictions (-1 for anomaly, 1 for normal)
            predictions = self.model.predict(features_scaled)
            anomaly_scores = self.model.score_samples(features_scaled)
            
            # Normalize anomaly scores to 0-1 range
            min_score = -anomaly_scores.max()
            max_score = -anomaly_scores.min()
            normalized_scores = (-anomaly_scores - min_score) / (max_score - min_score + 1e-10)
            
            # Overall anomaly detection rate
            anomaly_count = np.sum(predictions == -1)
            overall_anomaly_score = min(1.0, anomaly_count / len(predictions))
            
            # Indices of detected anomalies
            anomaly_indices = np.where(predictions == -1)[0].tolist()
            
            return overall_anomaly_score, anomaly_indices
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return 0.0, []


class HealthRiskScorer:
    """Main risk scoring engine combining rule-based and ML approaches"""
    
    def __init__(self):
        self.trend_detector = HealthTrendDetector()
        self.rule_assessor = RuleBasedRiskAssessment()
        self.ml_detector = MLAnomalyDetector()
        self.scaler = StandardScaler()
    
    def train_on_history(self, health_records: List) -> bool:
        """
        Train ML models on historical health data
        Args: List of HealthDataRecord objects
        """
        if not health_records or len(health_records) < 20:
            logger.warning("Insufficient historical data for training")
            return False
        
        # Extract metrics from records
        historical_data = []
        for record in health_records:
            # Get metrics from JSON field or use defaults
            metrics = record.metrics or {}
            
            historical_data.append({
                'heart_rate': metrics.get('heart_rate', 75),
                'temperature': metrics.get('temperature', 37.0),
                'blood_pressure_sys': metrics.get('blood_pressure_systolic', 120),
                'blood_pressure_dia': metrics.get('blood_pressure_diastolic', 80),
                'oxygen_saturation': metrics.get('oxygen_saturation', 98),
                'glucose_level': metrics.get('glucose_level', 100),
                'respiratory_rate': metrics.get('respiratory_rate', 16)
            })
        
        # Train ML detector
        return self.ml_detector.train(historical_data)
    
    def score_health_status(
        self,
        current_metrics: Dict[str, float],
        recent_history: Optional[List[Dict[str, float]]] = None,
        all_history: Optional[List[Dict[str, float]]] = None
    ) -> RiskScore:
        """
        Generate comprehensive health risk score
        
        Args:
            current_metrics: Current health metrics
            recent_history: Last 10-20 recent measurements
            all_history: Full historical data
        
        Returns:
            RiskScore object with detailed assessment
        """
        try:
            timestamp = datetime.now().isoformat()
            recommendations = []
            trend_analysis = {}
            all_risk_factors = []
            
            # 1. RULE-BASED ASSESSMENT (40% weight)
            rule_risk, rule_score, rule_factors = self.rule_assessor.assess_combination(current_metrics)
            all_risk_factors.extend(rule_factors)
            rule_weight = 0.4
            
            # 2. TREND ANALYSIS (30% weight)
            trend_weight = 0.3
            trend_score = 0.1
            
            if recent_history and len(recent_history) >= 3:
                metric_trends = {}
                for metric_name in current_metrics.keys():
                    values = [m.get(metric_name, current_metrics[metric_name]) for m in recent_history]
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
            
            # 3. ANOMALY DETECTION (20% weight)
            anomaly_weight = 0.2
            anomaly_score = 0.0
            
            if self.ml_detector.is_trained and recent_history:
                anomaly_score, anomaly_indices = self.ml_detector.detect_anomalies(recent_history)
                
                if anomaly_score > 0.3:
                    recommendations.append("🤖 ML: Unusual pattern detected in recent measurements")
            
            # 4. VOLATILITY ANALYSIS (10% weight)
            volatility_weight = 0.1
            volatility_score = 0.0
            
            if recent_history and len(recent_history) >= 5:
                volatilities = {}
                for metric_name in current_metrics.keys():
                    values = [m.get(metric_name, current_metrics[metric_name]) for m in recent_history]
                    volatility = self.trend_detector.calculate_volatility(values)
                    volatilities[metric_name] = volatility
                    
                    if volatility > 0.3:
                        volatility_score += volatility / len(current_metrics) * 0.5
                        recommendations.append(f"📊 High variability in {metric_name.replace('_', ' ')}")
            
            # 5. COMBINED SCORING
            weighted_score = (
                rule_score * rule_weight +
                trend_score * trend_weight +
                anomaly_score * anomaly_weight +
                volatility_score * volatility_weight
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
    
    Args:
        health_records: All health records
        current_index: Index of record to assess (default: latest)
    
    Returns:
        Risk assessment dictionary
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
    
    if not scorer.ml_detector.is_trained and len(health_records) >= 20:
        scorer.train_on_history(health_records)
    
    # Generate risk score
    risk_score = scorer.score_health_status(
        current_metrics=current_metrics,
        recent_history=recent_history,
        all_history=recent_history
    )
    
    return scorer.get_risk_summary(risk_score)
