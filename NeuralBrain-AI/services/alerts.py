"""
Alert System - Early Warning & Detection
Detects anomalies, spikes, and high-risk situations
Simplified for Python 3.14 (No Numpy)
"""

import logging
import math
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts"""
    SPIKE_DETECTED = "spike_detected"
    TREND_DETERIORATION = "trend_deterioration"
    HIGH_RISK_SCORE = "high_risk_score"
    ANOMALY_DETECTED = "anomaly_detected"
    DATA_QUALITY_ISSUE = "data_quality_issue"
    SYSTEM_ERROR = "system_error"


class Alert:
    """Represents a single alert"""
    
    def __init__(self, alert_type: AlertType, severity: AlertSeverity, 
                 title: str, message: str, data: Dict = None):
        """Initialize an alert."""
        self.id = self._generate_id()
        self.type = alert_type
        self.severity = severity
        self.title = title
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.utcnow()
        self.acknowledged = False
        self.acknowledged_at = None
        self.acknowledged_by = None
    
    @staticmethod
    def _generate_id() -> str:
        """Generate unique alert ID"""
        return f"alert_{uuid.uuid4().hex[:12]}"
    
    def to_dict(self) -> Dict:
        """Convert alert to dictionary"""
        return {
            'id': self.id,
            'type': self.type.value,
            'severity': self.severity.value,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'acknowledged': self.acknowledged,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by
        }
    
    def acknowledge(self, user_id: str = None) -> None:
        """Mark alert as acknowledged"""
        self.acknowledged = True
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = user_id


class SpikeDetector:
    """Detects sudden spikes in health metrics using pure Python"""
    
    def __init__(self, spike_threshold: float = 2.0):
        self.spike_threshold = spike_threshold
    
    def detect_spike(self, current_value: float, historical_values: List[float],
                     metric_name: str = "metric") -> Optional[Alert]:
        """Detect if current value is a spike compared to history."""
        if len(historical_values) < 3:
            return None
        
        # Calculate mean
        mean = sum(historical_values) / len(historical_values)
        
        # Calculate std dev
        variance = sum((x - mean) ** 2 for x in historical_values) / len(historical_values)
        std = math.sqrt(variance)
        
        if std == 0:
            return None
        
        z_score = abs((current_value - mean) / std)
        
        if z_score > self.spike_threshold:
            severity = AlertSeverity.HIGH if z_score > 3.5 else AlertSeverity.MEDIUM
            
            return Alert(
                alert_type=AlertType.SPIKE_DETECTED,
                severity=severity,
                title=f"Spike in {metric_name}",
                message=f"{metric_name} value ({current_value}) is {z_score:.1f} standard deviations above normal ({mean:.1f})",
                data={
                    'metric': metric_name,
                    'current_value': current_value,
                    'expected_mean': mean,
                    'std_dev': std,
                    'z_score': z_score
                }
            )
        
        return None


class TrendDetector:
    """Detects deteriorating health trends using pure Python"""
    
    def detect_trend_deterioration(self, values: List[float], metric_name: str = "metric",
                                   window_size: int = 7) -> Optional[Alert]:
        """Detect if trend is deteriorating (worsening)."""
        if len(values) < window_size:
            return None
        
        recent_values = values[-window_size:]
        n = len(recent_values)
        
        # Linear regression to find slope
        # x are indices 0, 1, 2...
        x = list(range(n))
        y = recent_values
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_xx = sum(x[i] ** 2 for i in range(n))
        
        denominator = (n * sum_xx - sum_x ** 2)
        
        if denominator == 0:
             slope = 0
        else:
             slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        # If slope is negative for health metrics, it's deteriorating
        # Note: This logic assumes 'deterioration' means decreasing value
        # For some metrics (like temperature/BP), increasing might be bad.
        # Keeping original logic for now (-0.1 threshold)
        if slope < -0.1:
            severity = AlertSeverity.MEDIUM if slope > -0.5 else AlertSeverity.HIGH
            
            return Alert(
                alert_type=AlertType.TREND_DETERIORATION,
                severity=severity,
                title=f"Deteriorating {metric_name}",
                message=f"{metric_name} shows consistent deterioration trend (slope: {slope:.3f})",
                data={
                    'metric': metric_name,
                    'recent_values': recent_values,
                    'slope': slope,
                    'window_size': window_size
                }
            )
        
        return None


class RiskAlertGenerator:
    """Generates alerts based on AI risk scores"""
    
    @staticmethod
    def generate_risk_alert(risk_score: float, risk_level: str, 
                           patient_id: str = None) -> Optional[Alert]:
        """Generate alert based on risk score."""
        if risk_level == "High":
            return Alert(
                alert_type=AlertType.HIGH_RISK_SCORE,
                severity=AlertSeverity.CRITICAL,
                title="⚠️ High Health Risk Detected",
                message=f"AI risk assessment indicates HIGH risk level ({risk_score:.1f}%). "
                       "Immediate medical consultation recommended.",
                data={
                    'risk_score': risk_score,
                    'risk_level': risk_level,
                    'patient_id': patient_id
                }
            )
        elif risk_level == "Medium" and risk_score > 60:
            return Alert(
                alert_type=AlertType.HIGH_RISK_SCORE,
                severity=AlertSeverity.HIGH,
                title="⚠️ Elevated Health Risk",
                message=f"Risk assessment shows elevated risk level ({risk_score:.1f}%). "
                       "Consider lifestyle adjustments and medical monitoring.",
                data={
                    'risk_score': risk_score,
                    'risk_level': risk_level,
                    'patient_id': patient_id
                }
            )
        
        return None


class AlertManager:
    """Central alert management system"""
    
    def __init__(self):
        """Initialize alert manager"""
        self.alerts: List[Alert] = []
        self.spike_detector = SpikeDetector()
        self.trend_detector = TrendDetector()
        self.risk_alert_generator = RiskAlertGenerator()
    
    def add_alert(self, alert: Alert) -> None:
        """Add alert to system"""
        # Checks for duplicate recent alerts to avoid spam
        # (Simple deduplication logic could be added here)
        self.alerts.append(alert)
        logger.warning(f"🚨 Alert: {alert.title} [{alert.severity.value}]")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get unacknowledged alerts"""
        return [a for a in self.alerts if not a.acknowledged]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get alerts of specific severity"""
        return [a for a in self.alerts if a.severity == severity]
    
    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """Get alerts from last N hours"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [a for a in self.alerts if a.timestamp > cutoff]
    
    def acknowledge_alert(self, alert_id: str, user_id: str = None) -> bool:
        """Acknowledge specific alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledge(user_id)
                return True
        return False
    
    def clear_old_alerts(self, days: int = 30) -> int:
        """Remove alerts older than N days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        original_count = len(self.alerts)
        self.alerts = [a for a in self.alerts if a.timestamp > cutoff]
        removed = original_count - len(self.alerts)
        logger.info(f"Cleared {removed} old alerts")
        return removed
    
    def to_list(self) -> List[Dict]:
        """Convert all alerts to list of dicts"""
        return [a.to_dict() for a in self.alerts]


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get or create global alert manager"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
