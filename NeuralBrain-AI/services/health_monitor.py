"""
Health Monitoring System - Background Health Monitor

Features:
- Periodic health checks (5-minute intervals)
- Automatic provider failover detection
- Metrics collection and tracking
- Historical health data retention
- Thread-safe operations

Architecture:
- BackgroundHealthMonitor: Main monitoring class (runs in background thread)
- HealthMetrics: Tracks provider health statistics
- HealthStatus: Real-time health snapshot
- HealthHistory: Historical health data storage
"""

import threading
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ProviderHealthStatus(Enum):
    """Provider health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass
class HealthMetric:
    """Single health check metric"""
    provider: str
    timestamp: str
    status: str
    latency_ms: Optional[float]
    error_message: Optional[str]
    response_time_ms: Optional[float]
    
    def to_dict(self):
        return asdict(self)


@dataclass
class ProviderHealth:
    """Provider health statistics"""
    provider: str
    status: str  # healthy, degraded, unavailable, error
    last_check: str
    check_count: int
    success_count: int
    failure_count: int
    error_rate: float  # 0-100%
    avg_latency_ms: float
    last_error: Optional[str]
    is_locked: bool
    consecutive_failures: int


class HealthMetricsCollector:
    """Collects and aggregates health metrics"""
    
    def __init__(self, history_size: int = 1000):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=history_size))
        self.lock = threading.Lock()
        self.history_size = history_size
    
    def record_health_check(
        self,
        provider: str,
        status: bool,
        latency_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        response_time_ms: Optional[float] = None
    ) -> None:
        """Record a health check result"""
        metric = HealthMetric(
            provider=provider,
            timestamp=datetime.utcnow().isoformat(),
            status="success" if status else "failure",
            latency_ms=latency_ms,
            error_message=error_message,
            response_time_ms=response_time_ms
        )
        
        with self.lock:
            self.metrics[provider].append(metric)
        
        logger.info(
            f"📊 Health check recorded | Provider: {provider} | "
            f"Status: {'✅' if status else '❌'} | "
            f"Latency: {latency_ms}ms" if latency_ms else ""
        )
    
    def get_provider_stats(self, provider: str, window_seconds: int = 300) -> Dict:
        """Get provider statistics for time window"""
        with self.lock:
            if provider not in self.metrics or not self.metrics[provider]:
                return {
                    "provider": provider,
                    "check_count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "error_rate": 0.0,
                    "avg_latency_ms": 0.0
                }
            
            # Get metrics within time window
            cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
            recent_metrics = [
                m for m in self.metrics[provider]
                if datetime.fromisoformat(m.timestamp) > cutoff_time
            ]
            
            if not recent_metrics:
                return {
                    "provider": provider,
                    "check_count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "error_rate": 0.0,
                    "avg_latency_ms": 0.0
                }
            
            success_count = sum(1 for m in recent_metrics if m.status == "success")
            failure_count = len(recent_metrics) - success_count
            
            latencies = [m.latency_ms for m in recent_metrics if m.latency_ms]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
            
            error_rate = (failure_count / len(recent_metrics) * 100) if recent_metrics else 0.0
            
            return {
                "provider": provider,
                "check_count": len(recent_metrics),
                "success_count": success_count,
                "failure_count": failure_count,
                "error_rate": round(error_rate, 2),
                "avg_latency_ms": round(avg_latency, 2)
            }
    
    def get_history(self, provider: str, limit: int = 100) -> List[Dict]:
        """Get metric history for provider"""
        with self.lock:
            if provider not in self.metrics:
                return []
            
            metrics_list = list(self.metrics[provider])[-limit:]
            return [m.to_dict() for m in metrics_list]
    
    def clear_old_metrics(self, older_than_seconds: int = 3600) -> None:
        """Clear metrics older than specified seconds"""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(seconds=older_than_seconds)
            
            for provider in self.metrics:
                # Keep only recent metrics
                recent = [
                    m for m in self.metrics[provider]
                    if datetime.fromisoformat(m.timestamp) > cutoff_time
                ]
                self.metrics[provider] = deque(recent, maxlen=self.history_size)
        
        logger.info(f"🧹 Cleaned up metrics older than {older_than_seconds}s")


class BackgroundHealthMonitor:
    """Background health monitoring system"""
    
    def __init__(
        self,
        orchestrator=None,
        check_interval_seconds: int = 300,
        failure_threshold: int = 3,
        degradation_threshold: float = 50.0  # Error rate %
    ):
        """
        Initialize health monitor
        
        Args:
            orchestrator: ExtendedAIProviderOrchestrator instance
            check_interval_seconds: How often to check (default: 5 minutes)
            failure_threshold: Consecutive failures before failover
            degradation_threshold: Error rate % for degraded status
        """
        self.orchestrator = orchestrator
        self.check_interval = check_interval_seconds
        self.failure_threshold = failure_threshold
        self.degradation_threshold = degradation_threshold
        
        self.metrics_collector = HealthMetricsCollector()
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.provider_consecutive_failures: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()
        
        logger.info(
            f"🏥 Health Monitor initialized | "
            f"Interval: {check_interval_seconds}s | "
            f"Failure threshold: {failure_threshold} | "
            f"Degradation threshold: {degradation_threshold}%"
        )
    
    def start(self) -> None:
        """Start background health monitoring"""
        if self.is_running:
            logger.warning("⚠️ Health monitor already running")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="HealthMonitor"
        )
        self.monitor_thread.start()
        logger.info("✅ Health monitor started (background thread)")
    
    def stop(self) -> None:
        """Stop background health monitoring"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🛑 Health monitor stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop (runs in background thread)"""
        logger.info("🔄 Health monitoring loop started")
        
        while self.is_running:
            try:
                self._check_all_providers()
                self._detect_degradation()
                self._trigger_failover_if_needed()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"❌ Health monitor error: {e}", exc_info=True)
                time.sleep(self.check_interval)
    
    def _check_all_providers(self) -> None:
        """Check health of all providers"""
        if not self.orchestrator:
            return
        
        logger.info("🏥 Starting health check cycle...")
        
        for provider_name, provider in self.orchestrator.providers.items():
            try:
                # Check if provider is available
                is_available = provider.is_available()
                
                if not is_available:
                    self.metrics_collector.record_health_check(
                        provider_name,
                        False,
                        error_message="Provider not configured"
                    )
                    with self.lock:
                        self.provider_consecutive_failures[provider_name] += 1
                    continue
                
                # Perform health check
                start_time = time.time()
                health = provider.health_check()
                latency_ms = (time.time() - start_time) * 1000
                
                success = health.get("status") == "healthy"
                error_msg = health.get("error") if not success else None
                
                self.metrics_collector.record_health_check(
                    provider_name,
                    success,
                    latency_ms=latency_ms,
                    error_message=error_msg,
                    response_time_ms=latency_ms
                )
                
                # Update consecutive failures
                with self.lock:
                    if success:
                        self.provider_consecutive_failures[provider_name] = 0
                    else:
                        self.provider_consecutive_failures[provider_name] += 1
                
                status_emoji = "✅" if success else "❌"
                logger.info(
                    f"{status_emoji} {provider_name}: "
                    f"{'Healthy' if success else 'Unhealthy'} | "
                    f"Latency: {latency_ms:.0f}ms"
                )
                
            except Exception as e:
                logger.error(f"❌ Error checking {provider_name}: {e}")
                self.metrics_collector.record_health_check(
                    provider_name,
                    False,
                    error_message=str(e)
                )
                with self.lock:
                    self.provider_consecutive_failures[provider_name] += 1
    
    def _detect_degradation(self) -> None:
        """Detect provider degradation based on error rates"""
        if not self.orchestrator:
            return
        
        for provider_name in self.orchestrator.providers:
            stats = self.metrics_collector.get_provider_stats(provider_name)
            error_rate = stats.get("error_rate", 0)
            
            if error_rate >= self.degradation_threshold and stats.get("check_count", 0) > 0:
                logger.warning(
                    f"⚠️ Provider degradation detected: {provider_name} | "
                    f"Error rate: {error_rate}%"
                )
    
    def _trigger_failover_if_needed(self) -> None:
        """Trigger failover if provider has too many consecutive failures"""
        if not self.orchestrator:
            return
        
        current_provider = self.orchestrator.lock_manager.get_current_provider()
        
        with self.lock:
            consecutive_failures = self.provider_consecutive_failures.get(current_provider, 0)
        
        if consecutive_failures >= self.failure_threshold:
            logger.warning(
                f"🔄 Failover triggered: {current_provider} | "
                f"Consecutive failures: {consecutive_failures}"
            )
            self.orchestrator._trigger_failover()
    
    def get_provider_health(self, provider: str) -> ProviderHealth:
        """Get current health status for a provider"""
        stats = self.metrics_collector.get_provider_stats(provider)
        
        with self.lock:
            consecutive_failures = self.provider_consecutive_failures.get(provider, 0)
        
        # Determine status
        error_rate = stats.get("error_rate", 0)
        if error_rate >= 100:
            status = ProviderHealthStatus.UNAVAILABLE.value
        elif error_rate >= self.degradation_threshold:
            status = ProviderHealthStatus.DEGRADED.value
        elif error_rate == 0 and stats.get("check_count", 0) > 0:
            status = ProviderHealthStatus.HEALTHY.value
        else:
            status = ProviderHealthStatus.HEALTHY.value
        
        is_locked = (
            self.orchestrator and
            self.orchestrator.lock_manager.get_current_provider() == provider
        )
        
        # Get last error
        history = self.metrics_collector.get_history(provider, limit=1)
        last_error = history[0]["error_message"] if history and history[0].get("error_message") else None
        
        return ProviderHealth(
            provider=provider,
            status=status,
            last_check=datetime.utcnow().isoformat(),
            check_count=stats.get("check_count", 0),
            success_count=stats.get("success_count", 0),
            failure_count=stats.get("failure_count", 0),
            error_rate=stats.get("error_rate", 0),
            avg_latency_ms=stats.get("avg_latency_ms", 0),
            last_error=last_error,
            is_locked=is_locked,
            consecutive_failures=consecutive_failures
        )
    
    def get_all_providers_health(self) -> List[ProviderHealth]:
        """Get health status for all providers"""
        if not self.orchestrator:
            return []
        
        return [
            self.get_provider_health(provider_name)
            for provider_name in self.orchestrator.providers
        ]
    
    def get_health_summary(self) -> Dict:
        """Get overall health summary"""
        all_health = self.get_all_providers_health()
        
        healthy_count = sum(1 for h in all_health if h.status == ProviderHealthStatus.HEALTHY.value)
        degraded_count = sum(1 for h in all_health if h.status == ProviderHealthStatus.DEGRADED.value)
        unavailable_count = sum(1 for h in all_health if h.status == ProviderHealthStatus.UNAVAILABLE.value)
        
        current_provider = (
            self.orchestrator.lock_manager.get_current_provider()
            if self.orchestrator else None
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "is_monitoring": self.is_running,
            "current_provider": current_provider,
            "overall_status": "healthy" if degraded_count == 0 and unavailable_count == 0 else "degraded",
            "provider_stats": {
                "total": len(all_health),
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unavailable": unavailable_count
            },
            "providers": [asdict(h) for h in all_health]
        }
    
    def get_metrics_history(self, provider: str, limit: int = 100) -> List[Dict]:
        """Get metrics history for a provider"""
        return self.metrics_collector.get_history(provider, limit)


# Singleton instance
_health_monitor: Optional[BackgroundHealthMonitor] = None
_health_monitor_lock = threading.Lock()


def get_health_monitor(orchestrator=None) -> BackgroundHealthMonitor:
    """Get or create singleton health monitor instance"""
    global _health_monitor
    
    if _health_monitor is None:
        with _health_monitor_lock:
            if _health_monitor is None:
                _health_monitor = BackgroundHealthMonitor(orchestrator=orchestrator)
    
    return _health_monitor


def reset_health_monitor() -> None:
    """Reset health monitor (for testing)"""
    global _health_monitor
    with _health_monitor_lock:
        if _health_monitor:
            _health_monitor.stop()
        _health_monitor = None
