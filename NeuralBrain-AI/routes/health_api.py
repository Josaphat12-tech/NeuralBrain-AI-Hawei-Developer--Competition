"""
Health Monitoring API - REST Endpoints

Endpoints:
- GET /api/health/status - Overall system health
- GET /api/health/providers - All providers health
- GET /api/health/provider/<name> - Specific provider health
- GET /api/health/metrics - Recent metrics
- GET /api/health/history/<provider> - Provider history
- GET /api/dashboard - Dashboard summary
- GET /api/config/monitor - Monitor configuration
- POST /api/config/monitor - Update monitor config
"""

import logging
from flask import Blueprint, jsonify, request
from datetime import datetime

logger = logging.getLogger(__name__)

# Create blueprint
health_bp = Blueprint('health', __name__, url_prefix='/api/health')


def get_health_monitor():
    """Get health monitor instance"""
    try:
        from services.health_monitor import get_health_monitor as get_monitor
        return get_monitor()
    except Exception as e:
        logger.error(f"Error getting health monitor: {e}")
        return None


def get_orchestrator():
    """Get orchestrator instance"""
    try:
        from services.extended_orchestrator import get_extended_orchestrator
        return get_extended_orchestrator()
    except Exception as e:
        logger.error(f"Error getting orchestrator: {e}")
        return None


# ============================================================================
# HEALTH STATUS ENDPOINTS
# ============================================================================

@health_bp.route('/status', methods=['GET'])
def get_health_status():
    """
    Get overall system health status
    
    Returns:
    {
        "status": "healthy",
        "timestamp": "2026-02-09T...",
        "is_monitoring": true,
        "current_provider": "openai",
        "provider_stats": {
            "total": 5,
            "healthy": 4,
            "degraded": 1,
            "unavailable": 0
        }
    }
    """
    try:
        monitor = get_health_monitor()
        if not monitor:
            return jsonify({
                "error": "Health monitor not initialized",
                "status": "unknown"
            }), 503
        
        summary = monitor.get_health_summary()
        return jsonify(summary), 200
    
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return jsonify({"error": str(e)}), 500


@health_bp.route('/providers', methods=['GET'])
def get_all_providers_health():
    """
    Get health status for all providers
    
    Returns:
    {
        "timestamp": "2026-02-09T...",
        "providers": [
            {
                "provider": "openai",
                "status": "healthy",
                "error_rate": 0.0,
                "avg_latency_ms": 150.5,
                ...
            },
            ...
        ]
    }
    """
    try:
        monitor = get_health_monitor()
        if not monitor:
            return jsonify({"error": "Health monitor not initialized"}), 503
        
        providers_health = monitor.get_all_providers_health()
        
        return jsonify({
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(providers_health),
            "providers": [
                {
                    "provider": h.provider,
                    "status": h.status,
                    "last_check": h.last_check,
                    "check_count": h.check_count,
                    "success_count": h.success_count,
                    "failure_count": h.failure_count,
                    "error_rate": h.error_rate,
                    "avg_latency_ms": h.avg_latency_ms,
                    "last_error": h.last_error,
                    "is_locked": h.is_locked,
                    "consecutive_failures": h.consecutive_failures
                }
                for h in providers_health
            ]
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting providers health: {e}")
        return jsonify({"error": str(e)}), 500


@health_bp.route('/provider/<provider_name>', methods=['GET'])
def get_provider_health(provider_name):
    """
    Get health status for specific provider
    
    Args:
        provider_name: Name of provider (openai, gemini, groq, cloudflare, huggingface)
    
    Returns:
    {
        "provider": "openai",
        "status": "healthy",
        "error_rate": 0.0,
        "avg_latency_ms": 150.5,
        ...
    }
    """
    try:
        monitor = get_health_monitor()
        if not monitor:
            return jsonify({"error": "Health monitor not initialized"}), 503
        
        health = monitor.get_provider_health(provider_name)
        
        return jsonify({
            "provider": health.provider,
            "status": health.status,
            "last_check": health.last_check,
            "check_count": health.check_count,
            "success_count": health.success_count,
            "failure_count": health.failure_count,
            "error_rate": health.error_rate,
            "avg_latency_ms": health.avg_latency_ms,
            "last_error": health.last_error,
            "is_locked": health.is_locked,
            "consecutive_failures": health.consecutive_failures
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting provider health: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# METRICS ENDPOINTS
# ============================================================================

@health_bp.route('/metrics', methods=['GET'])
def get_recent_metrics():
    """
    Get recent metrics from all providers
    
    Query params:
        - limit: Number of recent metrics per provider (default: 20)
    
    Returns:
    {
        "timestamp": "2026-02-09T...",
        "providers": {
            "openai": [
                {
                    "timestamp": "2026-02-09T...",
                    "status": "success",
                    "latency_ms": 150.5,
                    "error_message": null
                },
                ...
            ],
            ...
        }
    }
    """
    try:
        monitor = get_health_monitor()
        if not monitor:
            return jsonify({"error": "Health monitor not initialized"}), 503
        
        limit = request.args.get('limit', 20, type=int)
        orch = get_orchestrator()
        
        if not orch:
            return jsonify({"error": "Orchestrator not initialized"}), 503
        
        metrics_by_provider = {}
        for provider_name in orch.providers.keys():
            metrics = monitor.get_metrics_history(provider_name, limit=limit)
            metrics_by_provider[provider_name] = metrics
        
        return jsonify({
            "timestamp": datetime.utcnow().isoformat(),
            "limit": limit,
            "providers": metrics_by_provider
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({"error": str(e)}), 500


@health_bp.route('/history/<provider_name>', methods=['GET'])
def get_provider_history(provider_name):
    """
    Get historical metrics for specific provider
    
    Query params:
        - limit: Number of records to return (default: 100)
    
    Returns:
    {
        "provider": "openai",
        "timestamp": "2026-02-09T...",
        "count": 50,
        "metrics": [...]
    }
    """
    try:
        monitor = get_health_monitor()
        if not monitor:
            return jsonify({"error": "Health monitor not initialized"}), 503
        
        limit = request.args.get('limit', 100, type=int)
        history = monitor.get_metrics_history(provider_name, limit=limit)
        
        return jsonify({
            "provider": provider_name,
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(history),
            "metrics": history
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting provider history: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@health_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """
    Get comprehensive dashboard data
    
    Returns:
    {
        "timestamp": "2026-02-09T...",
        "system": {
            "status": "healthy",
            "is_monitoring": true,
            "current_provider": "openai"
        },
        "providers": {...},
        "statistics": {
            "total_checks": 5000,
            "avg_error_rate": 2.5,
            "avg_latency_ms": 175.3
        },
        "alerts": [...]
    }
    """
    try:
        monitor = get_health_monitor()
        orch = get_orchestrator()
        
        if not monitor or not orch:
            return jsonify({"error": "System not initialized"}), 503
        
        summary = monitor.get_health_summary()
        all_providers = monitor.get_all_providers_health()
        
        # Calculate statistics
        total_checks = sum(p.check_count for p in all_providers)
        avg_error_rate = (
            sum(p.error_rate for p in all_providers) / len(all_providers)
            if all_providers else 0
        )
        avg_latency = (
            sum(p.avg_latency_ms for p in all_providers) / len(all_providers)
            if all_providers else 0
        )
        
        # Detect alerts
        alerts = []
        for provider in all_providers:
            if provider.status == "unavailable":
                alerts.append({
                    "level": "critical",
                    "provider": provider.provider,
                    "message": f"{provider.provider} is unavailable (100% error rate)"
                })
            elif provider.status == "degraded":
                alerts.append({
                    "level": "warning",
                    "provider": provider.provider,
                    "message": f"{provider.provider} degraded ({provider.error_rate:.1f}% error rate)"
                })
        
        return jsonify({
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "status": summary["overall_status"],
                "is_monitoring": summary["is_monitoring"],
                "current_provider": summary["current_provider"]
            },
            "provider_stats": summary["provider_stats"],
            "providers": summary["providers"],
            "statistics": {
                "total_checks": total_checks,
                "avg_error_rate": round(avg_error_rate, 2),
                "avg_latency_ms": round(avg_latency, 2),
                "provider_count": len(all_providers)
            },
            "alerts": alerts
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# CONFIGURATION ENDPOINTS
# ============================================================================

@health_bp.route('/config/monitor', methods=['GET'])
def get_monitor_config():
    """
    Get current health monitor configuration
    
    Returns:
    {
        "check_interval_seconds": 300,
        "failure_threshold": 3,
        "degradation_threshold": 50.0,
        "is_running": true
    }
    """
    try:
        monitor = get_health_monitor()
        if not monitor:
            return jsonify({"error": "Health monitor not initialized"}), 503
        
        return jsonify({
            "check_interval_seconds": monitor.check_interval,
            "failure_threshold": monitor.failure_threshold,
            "degradation_threshold": monitor.degradation_threshold,
            "is_running": monitor.is_running
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting monitor config: {e}")
        return jsonify({"error": str(e)}), 500


@health_bp.route('/config/monitor', methods=['POST'])
def update_monitor_config():
    """
    Update health monitor configuration
    
    Request body:
    {
        "check_interval_seconds": 300,
        "failure_threshold": 3,
        "degradation_threshold": 50.0
    }
    """
    try:
        monitor = get_health_monitor()
        if not monitor:
            return jsonify({"error": "Health monitor not initialized"}), 503
        
        data = request.get_json() or {}
        
        # Update configurable parameters
        if "check_interval_seconds" in data:
            monitor.check_interval = data["check_interval_seconds"]
            logger.info(f"Updated check interval to {data['check_interval_seconds']}s")
        
        if "failure_threshold" in data:
            monitor.failure_threshold = data["failure_threshold"]
            logger.info(f"Updated failure threshold to {data['failure_threshold']}")
        
        if "degradation_threshold" in data:
            monitor.degradation_threshold = data["degradation_threshold"]
            logger.info(f"Updated degradation threshold to {data['degradation_threshold']}%")
        
        return jsonify({
            "message": "Configuration updated",
            "check_interval_seconds": monitor.check_interval,
            "failure_threshold": monitor.failure_threshold,
            "degradation_threshold": monitor.degradation_threshold
        }), 200
    
    except Exception as e:
        logger.error(f"Error updating monitor config: {e}")
        return jsonify({"error": str(e)}), 500


@health_bp.route('/control/start', methods=['POST'])
def start_monitoring():
    """Start health monitoring"""
    try:
        monitor = get_health_monitor()
        if not monitor:
            return jsonify({"error": "Health monitor not initialized"}), 503
        
        monitor.start()
        return jsonify({"message": "Health monitoring started", "is_running": True}), 200
    
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        return jsonify({"error": str(e)}), 500


@health_bp.route('/control/stop', methods=['POST'])
def stop_monitoring():
    """Stop health monitoring"""
    try:
        monitor = get_health_monitor()
        if not monitor:
            return jsonify({"error": "Health monitor not initialized"}), 503
        
        monitor.stop()
        return jsonify({"message": "Health monitoring stopped", "is_running": False}), 200
    
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@health_bp.route('/system', methods=['GET'])
def get_system_info():
    """
    Get system information
    
    Returns:
    {
        "timestamp": "2026-02-09T...",
        "version": "1.0.0",
        "providers_available": 5,
        "monitoring_active": true,
        "components": [...]
    }
    """
    try:
        orch = get_orchestrator()
        monitor = get_health_monitor()
        
        components = [
            {"name": "Extended Orchestrator", "status": "active" if orch else "inactive"},
            {"name": "Health Monitor", "status": "active" if monitor and monitor.is_running else "inactive"},
            {"name": "Lock System", "status": "active" if orch and orch.lock_manager else "inactive"},
            {"name": "Bottleneck Engine", "status": "active"}
        ]
        
        return jsonify({
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "providers_available": len(orch.providers) if orch else 0,
            "monitoring_active": monitor.is_running if monitor else False,
            "components": components
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return jsonify({"error": str(e)}), 500


def register_health_blueprint(app):
    """Register health monitoring blueprint with Flask app"""
    app.register_blueprint(health_bp)
    logger.info("✅ Health monitoring API endpoints registered")
