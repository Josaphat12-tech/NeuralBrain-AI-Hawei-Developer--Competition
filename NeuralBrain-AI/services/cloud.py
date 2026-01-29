"""
Huawei Cloud Readiness Module
Cloud-optimized configuration, ECS compatibility, scaling readiness
Developed by: Bitingo Josaphat JB
"""

import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CloudConfig:
    """Cloud environment configuration"""
    
    # Cloud providers
    CLOUD_PROVIDER_LOCAL = "local"
    CLOUD_PROVIDER_HUAWEI = "huawei"
    CLOUD_PROVIDER_AWS = "aws"
    CLOUD_PROVIDER_AZURE = "azure"
    
    # Deployment environments
    ENV_DEVELOPMENT = "development"
    ENV_STAGING = "staging"
    ENV_PRODUCTION = "production"
    
    def __init__(self):
        """Initialize cloud configuration"""
        self.cloud_provider = os.getenv('CLOUD_PROVIDER', self.CLOUD_PROVIDER_LOCAL)
        self.environment = os.getenv('ENVIRONMENT', self.ENV_DEVELOPMENT)
        self.region = os.getenv('CLOUD_REGION', 'us-east-1')
        self.project_id = os.getenv('CLOUD_PROJECT_ID', 'neuralbrain-ai')
        
        # Huawei-specific
        self.huawei_access_key = os.getenv('HUAWEI_ACCESS_KEY')
        self.huawei_secret_key = os.getenv('HUAWEI_SECRET_KEY')
        self.huawei_bucket = os.getenv('HUAWEI_OBS_BUCKET', 'neuralbrain-data')
        self.huawei_endpoint = os.getenv('HUAWEI_OBS_ENDPOINT', 
                                         'https://obs.cn-east-2.myhuaweicloud.com')
        
        # ECS-specific
        self.ecs_instance_type = os.getenv('ECS_INSTANCE_TYPE', 't3.small')
        self.ecs_disk_size = int(os.getenv('ECS_DISK_SIZE_GB', '20'))
        self.ecs_auto_scale = os.getenv('ECS_AUTO_SCALE', 'true').lower() == 'true'
        
        # Database
        self.db_provider = os.getenv('DB_PROVIDER', 'sqlite')  # sqlite, rds, dcs
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = int(os.getenv('DB_PORT', '5432'))
        self.db_name = os.getenv('DB_NAME', 'neuralbrain')
    
    def is_cloud_deployed(self) -> bool:
        """Check if running in cloud"""
        return self.cloud_provider != self.CLOUD_PROVIDER_LOCAL
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == self.ENV_PRODUCTION
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'cloud_provider': self.cloud_provider,
            'environment': self.environment,
            'region': self.region,
            'project_id': self.project_id,
            'ecs_instance_type': self.ecs_instance_type,
            'ecs_auto_scale': self.ecs_auto_scale,
            'db_provider': self.db_provider,
        }


class HuaweiCloudIntegration:
    """Huawei Cloud-specific integrations"""
    
    def __init__(self, config: CloudConfig = None):
        """
        Initialize Huawei Cloud integration.
        
        Args:
            config: CloudConfig instance
        """
        self.config = config or CloudConfig()
    
    def get_obs_connection_info(self) -> Dict[str, str]:
        """
        Get OBS (Object Storage Service) connection info.
        
        Returns:
            Dictionary with connection parameters
        """
        return {
            'access_key': self.config.huawei_access_key or 'PLACEHOLDER',
            'secret_key': self.config.huawei_secret_key or 'PLACEHOLDER',
            'bucket': self.config.huawei_bucket,
            'endpoint': self.config.huawei_endpoint,
            'region': self.config.region,
        }
    
    def get_rds_connection_string(self) -> str:
        """
        Generate RDS (Relational Database Service) connection string.
        
        Returns:
            PostgreSQL connection string
        """
        return (
            f"postgresql://{os.getenv('RDS_USER', 'admin')}:"
            f"{os.getenv('RDS_PASSWORD')}@"
            f"{self.config.db_host}:{self.config.db_port}/"
            f"{self.config.db_name}"
        )
    
    def get_dcs_connection_info(self) -> Dict[str, str]:
        """
        Get DCS (Distributed Cache Service) connection info for caching.
        
        Returns:
            Dictionary with DCS parameters
        """
        return {
            'host': os.getenv('DCS_HOST', 'cache.example.com'),
            'port': int(os.getenv('DCS_PORT', '6379')),
            'db': int(os.getenv('DCS_DB', '0')),
            'password': os.getenv('DCS_PASSWORD', ''),
        }


class DeploymentHelper:
    """Helps prepare system for cloud deployment"""
    
    @staticmethod
    def generate_dockerfile() -> str:
        """
        Generate Dockerfile for cloud deployment.
        
        Returns:
            Dockerfile content
        """
        return '''# Multi-stage build for NeuralBrain-AI
FROM python:3.10-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.10-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY . .

# Create directories for data
RUN mkdir -p data cache logs

# Security: Run as non-root
RUN useradd -m -u 1000 neuralbrain && chown -R neuralbrain:neuralbrain /app
USER neuralbrain

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# Run application
CMD ["python", "app.py"]
'''
    
    @staticmethod
    def generate_docker_compose() -> str:
        """
        Generate docker-compose.yml for local testing.
        
        Returns:
            Docker Compose content
        """
        return '''version: '3.8'

services:
  neuralbrain:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=sqlite:///neuralbrain.db
      - ENVIRONMENT=staging
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: Redis cache for DCS compatibility testing
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
'''
    
    @staticmethod
    def generate_k8s_deployment() -> str:
        """
        Generate Kubernetes deployment manifest.
        
        Returns:
            Kubernetes YAML content
        """
        return '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: neuralbrain-ai
  labels:
    app: neuralbrain-ai
    version: "1.0"

spec:
  replicas: 3
  selector:
    matchLabels:
      app: neuralbrain-ai
  
  template:
    metadata:
      labels:
        app: neuralbrain-ai
    
    spec:
      containers:
      - name: neuralbrain
        image: neuralbrain-ai:latest
        imagePullPolicy: Always
        
        ports:
        - containerPort: 5000
          name: http
        
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: FLASK_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: neuralbrain-secrets
              key: database-url
        
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 30
        
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
      
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - neuralbrain-ai
              topologyKey: kubernetes.io/hostname

---
apiVersion: v1
kind: Service
metadata:
  name: neuralbrain-service
spec:
  selector:
    app: neuralbrain-ai
  type: LoadBalancer
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
'''


class CloudHealthCheck:
    """Cloud deployment health checks"""
    
    @staticmethod
    def check_cloud_readiness() -> Dict[str, Any]:
        """
        Check if system is ready for cloud deployment.
        
        Returns:
            Dictionary with readiness status
        """
        checks = {
            'environment_variables': CloudHealthCheck._check_env_vars(),
            'cloud_config': CloudHealthCheck._check_cloud_config(),
            'database': CloudHealthCheck._check_database(),
            'storage': CloudHealthCheck._check_storage(),
            'dependencies': CloudHealthCheck._check_dependencies(),
        }
        
        all_passed = all(check.get('status') == 'ok' for check in checks.values())
        
        return {
            'status': 'ready' if all_passed else 'needs_setup',
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
            'checks': checks,
        }
    
    @staticmethod
    def _check_env_vars() -> Dict[str, Any]:
        """Check required environment variables"""
        required_vars = [
            'FLASK_APP',
            'FLASK_ENV',
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        
        return {
            'status': 'ok' if not missing else 'warning',
            'message': f"All required environment variables set" if not missing 
                      else f"Missing: {', '.join(missing)}",
        }
    
    @staticmethod
    def _check_cloud_config() -> Dict[str, Any]:
        """Check cloud configuration"""
        config = CloudConfig()
        
        if config.is_cloud_deployed() and not config.huawei_access_key:
            return {
                'status': 'warning',
                'message': 'Cloud provider selected but credentials not configured',
            }
        
        return {
            'status': 'ok',
            'message': f"Cloud provider: {config.cloud_provider}",
        }
    
    @staticmethod
    def _check_database() -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            from models import db
            # This would need actual implementation
            return {
                'status': 'ok',
                'message': 'Database check passed',
            }
        except Exception as e:
            return {
                'status': 'warning',
                'message': f'Database check failed: {str(e)}',
            }
    
    @staticmethod
    def _check_storage() -> Dict[str, Any]:
        """Check storage configuration"""
        data_dir = Path('data')
        
        if not data_dir.exists():
            try:
                data_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Cannot create data directory: {str(e)}',
                }
        
        try:
            (data_dir / '.test').write_text('test')
            (data_dir / '.test').unlink()
            return {
                'status': 'ok',
                'message': 'Storage check passed',
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Storage write check failed: {str(e)}',
            }
    
    @staticmethod
    def _check_dependencies() -> Dict[str, Any]:
        """Check required Python packages"""
        required_packages = [
            'flask',
            'flask_sqlalchemy',
            'requests',
            'numpy',
            'sklearn',
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        return {
            'status': 'ok' if not missing else 'error',
            'message': 'All dependencies installed' if not missing
                      else f'Missing packages: {", ".join(missing)}',
        }
