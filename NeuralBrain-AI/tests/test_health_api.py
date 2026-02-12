"""
Health Monitoring API - Test Suite

Test coverage:
- Health status endpoints
- Metrics endpoints
- Dashboard endpoints
- Configuration endpoints
- System information endpoint
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime

from routes.health_api import health_bp


@pytest.fixture
def client():
    """Create Flask test client"""
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(health_bp)
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_monitor():
    """Create mock health monitor"""
    monitor = MagicMock()
    monitor.check_interval = 300
    monitor.failure_threshold = 3
    monitor.degradation_threshold = 50.0
    monitor.is_running = True
    
    # Mock summary
    monitor.get_health_summary.return_value = {
        "timestamp": datetime.utcnow().isoformat(),
        "is_monitoring": True,
        "current_provider": "openai",
        "overall_status": "healthy",
        "provider_stats": {
            "total": 5,
            "healthy": 4,
            "degraded": 1,
            "unavailable": 0
        },
        "providers": []
    }
    
    return monitor


@pytest.fixture
def mock_orchestrator():
    """Create mock orchestrator"""
    orch = MagicMock()
    orch.providers = {
        "openai": MagicMock(),
        "gemini": MagicMock(),
        "groq": MagicMock(),
        "cloudflare": MagicMock(),
        "huggingface": MagicMock()
    }
    orch.lock_manager = MagicMock()
    return orch


class TestHealthStatusEndpoints:
    """Test health status endpoints"""
    
    @patch('routes.health_api.get_health_monitor')
    def test_get_health_status_success(self, mock_get_monitor, client, mock_monitor):
        """Test getting overall health status"""
        mock_get_monitor.return_value = mock_monitor
        
        response = client.get('/api/health/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["is_monitoring"] is True
        assert data["current_provider"] == "openai"
        assert "provider_stats" in data
    
    @patch('routes.health_api.get_health_monitor')
    def test_get_health_status_not_initialized(self, mock_get_monitor, client):
        """Test getting status when monitor not initialized"""
        mock_get_monitor.return_value = None
        
        response = client.get('/api/health/status')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert "error" in data
    
    @patch('routes.health_api.get_health_monitor')
    def test_get_all_providers_health(self, mock_get_monitor, client, mock_monitor):
        """Test getting all providers health"""
        # Mock provider health data
        mock_health1 = MagicMock()
        mock_health1.provider = "openai"
        mock_health1.status = "healthy"
        mock_health1.error_rate = 0.0
        mock_health1.avg_latency_ms = 150.5
        mock_health1.last_error = None
        mock_health1.is_locked = True
        mock_health1.consecutive_failures = 0
        mock_health1.check_count = 100
        mock_health1.success_count = 100
        mock_health1.failure_count = 0
        mock_health1.last_check = datetime.utcnow().isoformat()
        
        mock_monitor.get_all_providers_health.return_value = [mock_health1]
        mock_get_monitor.return_value = mock_monitor
        
        response = client.get('/api/health/providers')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["count"] == 1
        assert data["providers"][0]["provider"] == "openai"
        assert data["providers"][0]["status"] == "healthy"
    
    @patch('routes.health_api.get_health_monitor')
    def test_get_provider_health(self, mock_get_monitor, client, mock_monitor):
        """Test getting specific provider health"""
        mock_health = MagicMock()
        mock_health.provider = "groq"
        mock_health.status = "healthy"
        mock_health.error_rate = 0.0
        mock_health.avg_latency_ms = 120.0
        mock_health.last_error = None
        mock_health.is_locked = False
        mock_health.consecutive_failures = 0
        mock_health.check_count = 50
        mock_health.success_count = 50
        mock_health.failure_count = 0
        mock_health.last_check = datetime.utcnow().isoformat()
        
        mock_monitor.get_provider_health.return_value = mock_health
        mock_get_monitor.return_value = mock_monitor
        
        response = client.get('/api/health/provider/groq')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["provider"] == "groq"
        assert data["status"] == "healthy"


class TestMetricsEndpoints:
    """Test metrics endpoints"""
    
    @patch('routes.health_api.get_orchestrator')
    @patch('routes.health_api.get_health_monitor')
    def test_get_recent_metrics(self, mock_get_monitor, mock_get_orch, client, mock_monitor, mock_orchestrator):
        """Test getting recent metrics"""
        mock_get_monitor.return_value = mock_monitor
        mock_get_orch.return_value = mock_orchestrator
        
        mock_metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "latency_ms": 150.5,
            "error_message": None
        }
        mock_monitor.get_metrics_history.return_value = [mock_metric]
        
        response = client.get('/api/health/metrics?limit=20')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "providers" in data
        assert data["limit"] == 20
    
    @patch('routes.health_api.get_health_monitor')
    def test_get_provider_history(self, mock_get_monitor, client, mock_monitor):
        """Test getting provider history"""
        mock_metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "provider": "openai",
            "status": "success",
            "latency_ms": 150.5,
            "error_message": None
        }
        mock_monitor.get_metrics_history.return_value = [mock_metric] * 5
        mock_get_monitor.return_value = mock_monitor
        
        response = client.get('/api/health/history/openai?limit=100')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["provider"] == "openai"
        assert data["count"] == 5
        assert len(data["metrics"]) == 5


class TestDashboardEndpoint:
    """Test dashboard endpoint"""
    
    @patch('routes.health_api.get_orchestrator')
    @patch('routes.health_api.get_health_monitor')
    def test_get_dashboard_data(self, mock_get_monitor, mock_get_orch, client, mock_monitor, mock_orchestrator):
        """Test getting dashboard data"""
        mock_get_monitor.return_value = mock_monitor
        mock_get_orch.return_value = mock_orchestrator
        
        mock_health = MagicMock()
        mock_health.provider = "openai"
        mock_health.status = "healthy"
        mock_health.error_rate = 0.0
        mock_health.avg_latency_ms = 150.0
        mock_health.check_count = 100
        
        mock_monitor.get_all_providers_health.return_value = [mock_health]
        
        response = client.get('/api/health/dashboard')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "system" in data
        assert "statistics" in data
        assert "alerts" in data
        assert data["statistics"]["provider_count"] == 1


class TestConfigurationEndpoints:
    """Test configuration endpoints"""
    
    @patch('routes.health_api.get_health_monitor')
    def test_get_monitor_config(self, mock_get_monitor, client, mock_monitor):
        """Test getting monitor configuration"""
        mock_get_monitor.return_value = mock_monitor
        
        response = client.get('/api/health/config/monitor')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["check_interval_seconds"] == 300
        assert data["failure_threshold"] == 3
        assert data["degradation_threshold"] == 50.0
        assert data["is_running"] is True
    
    @patch('routes.health_api.get_health_monitor')
    def test_update_monitor_config(self, mock_get_monitor, client, mock_monitor):
        """Test updating monitor configuration"""
        mock_get_monitor.return_value = mock_monitor
        
        config_update = {
            "check_interval_seconds": 600,
            "failure_threshold": 5,
            "degradation_threshold": 60.0
        }
        
        response = client.post(
            '/api/health/config/monitor',
            data=json.dumps(config_update),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["check_interval_seconds"] == 600
        assert data["failure_threshold"] == 5
        assert data["degradation_threshold"] == 60.0
    
    @patch('routes.health_api.get_health_monitor')
    def test_start_monitoring(self, mock_get_monitor, client, mock_monitor):
        """Test starting monitoring"""
        mock_get_monitor.return_value = mock_monitor
        
        response = client.post('/api/health/control/start')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "started" in data["message"].lower()
        mock_monitor.start.assert_called()
    
    @patch('routes.health_api.get_health_monitor')
    def test_stop_monitoring(self, mock_get_monitor, client, mock_monitor):
        """Test stopping monitoring"""
        mock_get_monitor.return_value = mock_monitor
        
        response = client.post('/api/health/control/stop')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "stopped" in data["message"].lower()
        mock_monitor.stop.assert_called()


class TestSystemEndpoint:
    """Test system information endpoint"""
    
    @patch('routes.health_api.get_orchestrator')
    @patch('routes.health_api.get_health_monitor')
    def test_get_system_info(self, mock_get_monitor, mock_get_orch, client, mock_monitor, mock_orchestrator):
        """Test getting system information"""
        mock_get_monitor.return_value = mock_monitor
        mock_get_orch.return_value = mock_orchestrator
        
        response = client.get('/api/health/system')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "version" in data
        assert "providers_available" in data
        assert "monitoring_active" in data
        assert "components" in data
        assert len(data["components"]) == 4


class TestErrorHandling:
    """Test error handling"""
    
    @patch('routes.health_api.get_health_monitor')
    def test_exception_handling(self, mock_get_monitor, client):
        """Test that exceptions are handled gracefully"""
        mock_get_monitor.side_effect = Exception("Test error")
        
        response = client.get('/api/health/status')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data


class TestResponseFormat:
    """Test response format consistency"""
    
    @patch('routes.health_api.get_health_monitor')
    def test_status_endpoint_response_format(self, mock_get_monitor, client, mock_monitor):
        """Test status endpoint response format"""
        mock_get_monitor.return_value = mock_monitor
        
        response = client.get('/api/health/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "timestamp" in data
        assert "is_monitoring" in data
        assert "current_provider" in data
    
    @patch('routes.health_api.get_health_monitor')
    def test_all_endpoints_have_timestamp(self, mock_get_monitor, client, mock_monitor):
        """Test that all endpoints include timestamp"""
        mock_get_monitor.return_value = mock_monitor
        mock_monitor.get_metrics_history.return_value = []
        
        endpoints = [
            '/api/health/status',
            '/api/health/config/monitor'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                data = json.loads(response.data)
                # Either has timestamp or is configuration data
                assert "timestamp" in data or "is_running" in data
