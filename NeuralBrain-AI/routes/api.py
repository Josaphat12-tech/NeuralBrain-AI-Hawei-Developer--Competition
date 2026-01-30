"""
NeuralBrain-AI REST API Routes
Endpoints for data ingestion, retrieval, alerts, and system management
Developed by: Bitingo Josaphat JB
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
import time
import logging
import requests
from models import db, HealthDataRecord, IngestionLog
from services.ingestion import DataIngestionService
from services.normalization import DataNormalizer
from services.validation import DataValidator
from services.risk_scoring import calculate_health_risk, get_risk_scorer
from services.alerts import get_alert_manager
from services.security import InputSanitizer, rate_limit
from services.offline import get_cache_manager, get_connection_status
from services.cloud import CloudConfig, CloudHealthCheck

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize services
ingestion_service = DataIngestionService()
normalizer = DataNormalizer()
validator = DataValidator()


@api_bp.route('/status', methods=['GET'])
def api_status():
    """
    GET /api/status
    Returns the current API status and system information.
    """
    return jsonify({
        'status': 'operational',
        'timestamp': datetime.utcnow().isoformat(),
        'app_name': current_app.config['APP_NAME'],
        'app_version': current_app.config['APP_VERSION'],
        'author': current_app.config['AUTHOR'],
        'endpoints': {
            'ingest': '/api/ingest',
            'data': '/api/data',
            'data_by_id': '/api/data/<id>',
            'logs': '/api/logs',
            'status': '/api/status'
        }
    }), 200


@api_bp.route('/ingest', methods=['POST', 'GET'])
def ingest_data():
    """
    GET/POST /api/ingest
    Triggers data ingestion from all configured health APIs.
    
    Returns:
        JSON response with ingestion results including:
        - timestamp: When ingestion occurred
        - total_apis: Number of APIs configured
        - successful: Number of successful API fetches
        - failed: Number of failed API fetches
        - sources: Detailed results per API
    """
    start_time = time.time()
    
    try:
        logger.info("=== Starting health data ingestion ===")
        
        # Perform ingestion
        ingestion_result = ingestion_service.ingest_all_sources()
        execution_time = time.time() - start_time
        ingestion_result['execution_time_seconds'] = round(execution_time, 2)
        
        # Log the ingestion operation
        for api_source, source_result in ingestion_result.get('sources', {}).items():
            log_entry = IngestionLog(
                api_source=api_source,
                status=source_result.get('status', 'unknown'),
                records_fetched=source_result.get('records', 0),
                records_processed=source_result.get('records', 0) if source_result.get('status') == 'success' else 0,
                error_message=source_result.get('error'),
                execution_time=execution_time,
                details={
                    'total_sources': ingestion_result['total_apis'],
                    'total_successful': ingestion_result['successful']
                }
            )
            db.session.add(log_entry)
        
        db.session.commit()
        
        logger.info(f"Ingestion completed: {ingestion_result['successful']} successful, {ingestion_result['failed']} failed")
        
        return jsonify({
            'status': 'success' if ingestion_result['failed'] == 0 else 'partial',
            'message': f"Ingestion complete: {ingestion_result['successful']} source(s) succeeded",
            'data': ingestion_result
        }), 200
        
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Ingestion failed',
            'error': str(e)
        }), 500


@api_bp.route('/data', methods=['GET'])
def get_data():
    """
    GET /api/data
    Returns normalized health data from the database.
    
    Query Parameters:
        - source: Filter by data source (optional)
        - status: Filter by record status - valid/invalid/pending (optional)
        - limit: Maximum records to return (default: 100)
        - offset: Starting record position (default: 0)
    
    Returns:
        JSON list of normalized health data records
    """
    try:
        source = request.args.get('source', type=str)
        status = request.args.get('status', type=str, default='valid')
        limit = request.args.get('limit', type=int, default=100)
        offset = request.args.get('offset', type=int, default=0)
        
        query = HealthDataRecord.query
        
        if source:
            query = query.filter_by(data_source=source)
        if status:
            query = query.filter_by(status=status)
        
        total_count = query.count()
        records = query.order_by(HealthDataRecord.timestamp.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'pagination': {
                'total': total_count,
                'returned': len(records),
                'limit': limit,
                'offset': offset
            },
            'data': [record.to_dict() for record in records]
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve data',
            'error': str(e)
        }), 500


@api_bp.route('/data/<int:record_id>', methods=['GET'])
def get_data_by_id(record_id):
    """
    GET /api/data/<id>
    Returns a specific health data record by ID.
    
    Returns:
        JSON object with the requested record or 404 if not found
    """
    try:
        record = HealthDataRecord.query.get_or_404(record_id)
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'data': record.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Record not found',
            'error': str(e)
        }), 404


@api_bp.route('/logs', methods=['GET'])
def get_ingestion_logs():
    """
    GET /api/logs
    Returns ingestion operation logs.
    
    Query Parameters:
        - source: Filter by API source (optional)
        - status: Filter by log status (optional)
        - limit: Maximum logs to return (default: 50)
    
    Returns:
        JSON list of ingestion logs
    """
    try:
        source = request.args.get('source', type=str)
        status = request.args.get('status', type=str)
        limit = request.args.get('limit', type=int, default=50)
        
        query = IngestionLog.query
        
        if source:
            query = query.filter_by(api_source=source)
        if status:
            query = query.filter_by(status=status)
        
        logs = query.order_by(IngestionLog.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'count': len(logs),
            'data': [log.to_dict() for log in logs]
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve logs: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve logs',
            'error': str(e)
        }), 500


@api_bp.route('/validate', methods=['POST'])
def validate_data():
    """
    POST /api/validate
    Validates health data against defined rules.
    
    Request Body:
        - data: Dictionary or list of health metrics
        - type: 'single' for dict or 'batch' for list
    
    Returns:
        JSON validation results
    """
    try:
        payload = request.get_json()
        
        if not payload:
            return jsonify({
                'status': 'error',
                'message': 'Invalid request body'
            }), 400
        
        data = payload.get('data')
        data_type = payload.get('type', 'single')
        
        if data_type == 'batch' and isinstance(data, list):
            results = validator.validate_batch(data)
        elif isinstance(data, dict):
            is_valid, errors = validator.validate_record(data)
            results = {
                'valid': is_valid,
                'errors': errors
            }
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid data format'
            }), 400
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'validation_result': results
        }), 200
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Validation failed',
            'error': str(e)
        }), 500


@api_bp.route('/analytics', methods=['GET'])
def analytics():
    """
    GET /api/analytics
    Returns analytics and aggregated health data for visualization.
    
    Returns:
        JSON with metrics summaries and statistics
    """
    try:
        from services.seed_data import DataSeeder
        
        # Get health metrics summary
        metrics_summary = DataSeeder.get_health_metrics_summary()
        
        # Get statistics
        api_stats = DataSeeder.get_statistics()
        
        # Get time-series data (last 7 days)
        records = HealthDataRecord.query.filter(
            HealthDataRecord.timestamp >= datetime.utcnow() - timedelta(days=7)
        ).order_by(HealthDataRecord.timestamp).all()
        
        # Group by date for time series
        time_series = {}
        for record in records:
            date_key = record.timestamp.strftime('%Y-%m-%d')
            if date_key not in time_series:
                time_series[date_key] = {'count': 0, 'valid': 0, 'invalid': 0}
            time_series[date_key]['count'] += 1
            if record.status == 'valid':
                time_series[date_key]['valid'] += 1
            else:
                time_series[date_key]['invalid'] += 1
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'metrics_summary': metrics_summary,
            'statistics': api_stats,
            'time_series': time_series,
            'recent_records': [r.to_dict() for r in records[-10:]],
            # Attempt to include a lightweight external data snapshot from a free public API
            'external_sources': external_sources if (external_sources := (lambda: (
                (lambda _resp: (_resp.json().get('entries', []) if _resp and _resp.ok else []))(
                    requests.get('https://api.publicapis.org/entries', timeout=3)
                )
            ))()) else {}
        }), 200
        
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve analytics',
            'error': str(e)
        }), 500


@api_bp.route('/health-risk', methods=['GET'])
def get_health_risk():
    """
    GET /api/health-risk
    AI-based health risk assessment for latest record
    
    Query Parameters:
        - record_id: (optional) Specific record to assess
    
    Returns risk score with:
        - Overall risk level (Low/Medium/High)
        - Risk percentage (0-100)
        - Risk factors
        - Trend analysis
        - Personalized recommendations
        - ML confidence score
    """
    try:
        record_id = request.args.get('record_id', type=int)
        
        # Get all health records
        if record_id:
            records = HealthDataRecord.query.filter_by(id=record_id).all()
            if not records:
                return jsonify({
                    'status': 'error',
                    'message': 'Record not found'
                }), 404
        else:
            records = HealthDataRecord.query.order_by(HealthDataRecord.timestamp).all()
        
        if not records:
            return jsonify({
                'status': 'error',
                'message': 'No health records available'
            }), 404
        
        # Calculate risk for latest record
        current_index = -1 if not record_id else 0
        risk_assessment = calculate_health_risk(records, current_index)
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'risk_assessment': risk_assessment
        }), 200
        
    except Exception as e:
        logger.error(f"Health risk error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to calculate health risk',
            'error': str(e)
        }), 500


@api_bp.route('/health-risk/batch', methods=['POST'])
def batch_health_risk():
    """
    POST /api/health-risk/batch
    Calculate risk for multiple records
    
    Request Body:
        {
            "record_ids": [1, 2, 3, ...]  or
            "limit": 10  (latest N records)
        }
    
    Returns:
        List of risk assessments for each record
    """
    try:
        data = request.get_json() or {}
        
        if 'record_ids' in data:
            records = HealthDataRecord.query.filter(
                HealthDataRecord.id.in_(data['record_ids'])
            ).order_by(HealthDataRecord.timestamp).all()
        else:
            limit = data.get('limit', 20)
            records = HealthDataRecord.query.order_by(
                HealthDataRecord.timestamp.desc()
            ).limit(limit).all()
            records = list(reversed(records))
        
        if not records:
            return jsonify({
                'status': 'error',
                'message': 'No records found'
            }), 404
        
        # Calculate risk for each record
        risk_assessments = []
        for idx in range(len(records)):
            risk = calculate_health_risk(records, idx)
            risk_assessments.append({
                'record_id': records[idx].id,
                'risk_assessment': risk
            })
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'count': len(risk_assessments),
            'assessments': risk_assessments
        }), 200
        
    except Exception as e:
        logger.error(f"Batch health risk error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to calculate batch risks',
            'error': str(e)
        }), 500


@api_bp.route('/health-risk/trends', methods=['GET'])
def get_risk_trends():
    """
    GET /api/health-risk/trends
    Get risk trend over time
    
    Query Parameters:
        - days: Number of days to analyze (default: 7)
        - interval: Hours between samples (default: 1)
    
    Returns:
        Risk scores over time with trend analysis
    """
    try:
        from datetime import timedelta
        from services.risk_scoring import HealthTrendDetector
        
        days = request.args.get('days', 7, type=int)
        interval = request.args.get('interval', 1, type=int)
        
        # Get records from last N days
        cutoff = datetime.utcnow() - timedelta(days=days)
        records = HealthDataRecord.query.filter(
            HealthDataRecord.timestamp >= cutoff
        ).order_by(HealthDataRecord.timestamp).all()
        
        if not records:
            return jsonify({
                'status': 'error',
                'message': 'No records in specified time range'
            }), 404
        
        # Calculate risk for each record
        trend_data = []
        all_risks = []
        
        for idx, record in enumerate(records):
            risk = calculate_health_risk(records, idx)
            trend_data.append({
                'timestamp': record.timestamp.isoformat(),
                'risk_score': risk['risk_percentage'],
                'risk_level': risk['overall_risk']
            })
            all_risks.append(risk['risk_percentage'])
        
        # Analyze trend
        trend_detector = HealthTrendDetector()
        trend, strength = trend_detector.detect_trend(all_risks)
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'period_days': days,
            'data_points': len(trend_data),
            'trend': {
                'direction': trend,
                'strength': round(strength, 2)
            },
            'statistics': {
                'avg_risk': round(sum(all_risks) / len(all_risks), 2),
                'min_risk': round(min(all_risks), 2),
                'max_risk': round(max(all_risks), 2)
            },
            'trend_data': trend_data
        }), 200
        
    except Exception as e:
        logger.error(f"Risk trends error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve risk trends',
            'error': str(e)
        }), 500


@api_bp.route('/ai/model-info', methods=['GET'])
def get_ai_model_info():
    """
    GET /api/ai/model-info
    Get information about the AI risk scoring model
    
    Returns:
        Model architecture, features, and performance metrics
    """
    try:
        scorer = get_risk_scorer()
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'model': {
                'name': 'NeuralBrain Health Risk Scorer v1.0',
                'approach': 'Hybrid Rule-Based + Machine Learning',
                'algorithms': [
                    'Rule-Based Assessment (40% weight)',
                    'Trend Detection (30% weight)',
                    'Isolation Forest Anomaly Detection (20% weight)',
                    'Volatility Analysis (10% weight)'
                ],
                'features': [
                    'heart_rate',
                    'temperature',
                    'blood_pressure_systolic',
                    'blood_pressure_diastolic',
                    'oxygen_saturation',
                    'glucose_level',
                    'respiratory_rate'
                ],
                'ml_trained': scorer.ml_detector.is_trained,
                'risk_levels': ['Low', 'Medium', 'High'],
                'output': {
                    'overall_risk': 'Categorical risk level',
                    'risk_percentage': 'Numeric risk score (0-100)',
                    'risk_factors': 'Metrics exceeding safe ranges',
                    'trend_analysis': 'Trend direction and strength',
                    'recommendations': 'Personalized health suggestions',
                    'confidence': 'Model confidence (0-1)'
                },
                'explainability': 'All risk factors are explained with specific metrics and thresholds',
                'transparency': 'No black-box predictions - all decisions are traceable',
                'privacy': 'Runs locally - no data sent to external services'
            },
            'clinical_ranges': {
                'heart_rate': {'normal': [60, 100], 'unit': 'bpm'},
                'temperature': {'normal': [36.5, 37.5], 'unit': '°C'},
                'blood_pressure': {'normal': '120/80', 'unit': 'mmHg'},
                'oxygen_saturation': {'normal': [95, 100], 'unit': '%'},
                'glucose_level': {'normal': [70, 100], 'unit': 'mg/dL'},
                'respiratory_rate': {'normal': [12, 20], 'unit': 'breaths/min'}
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Model info error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve model information',
            'error': str(e)
        }), 500


# ================================================================================
# FEATURE 3: ALERT SYSTEM ENDPOINTS
# ================================================================================

@api_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """
    GET /api/alerts
    Retrieve all active alerts or recent alerts.
    
    Query Parameters:
        - severity: Filter by severity (low, medium, high, critical)
        - hours: Get alerts from last N hours (default: 24)
        - active_only: Only unacknowledged alerts (default: true)
    """
    try:
        alert_manager = get_alert_manager()
        
        severity = request.args.get('severity')
        hours = int(request.args.get('hours', 24))
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        if active_only:
            alerts = alert_manager.get_active_alerts()
        else:
            alerts = alert_manager.get_recent_alerts(hours)
        
        if severity:
            from services.alerts import AlertSeverity
            try:
                severity_enum = AlertSeverity(severity)
                alerts = [a for a in alerts if a.severity == severity_enum]
            except ValueError:
                pass
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'total_alerts': len(alerts),
            'alerts': [a.to_dict() for a in alerts]
        }), 200
    
    except Exception as e:
        logger.error(f"Get alerts error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """
    POST /api/alerts/<alert_id>/acknowledge
    Mark an alert as acknowledged.
    """
    try:
        alert_manager = get_alert_manager()
        user_id = request.json.get('user_id') if request.json else None
        
        success = alert_manager.acknowledge_alert(alert_id, user_id)
        
        return jsonify({
            'status': 'success' if success else 'not_found',
            'alert_id': alert_id,
            'acknowledged': success
        }), 200 if success else 404
    
    except Exception as e:
        logger.error(f"Acknowledge alert error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ================================================================================
# FEATURE 9: OFFLINE-FIRST SUPPORT ENDPOINTS
# ================================================================================

@api_bp.route('/offline/status', methods=['GET'])
def offline_status():
    """
    GET /api/offline/status
    Check system connectivity and offline status.
    """
    try:
        connection_status = get_connection_status()
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'connection': connection_status.get_status()
        }), 200
    
    except Exception as e:
        logger.error(f"Offline status error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/cache/<key>', methods=['GET'])
def get_cache(key):
    """
    GET /api/cache/<key>
    Retrieve cached value.
    """
    try:
        cache_manager = get_cache_manager()
        sanitized_key = InputSanitizer.sanitize_string(key)
        value = cache_manager.get(sanitized_key)
        
        if value is None:
            return jsonify({'status': 'not_found'}), 404
        
        return jsonify({
            'status': 'success',
            'key': sanitized_key,
            'value': value
        }), 200
    
    except Exception as e:
        logger.error(f"Cache get error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ================================================================================
# FEATURE 10: CLOUD READINESS ENDPOINTS
# ================================================================================

@api_bp.route('/cloud/status', methods=['GET'])
def cloud_status():
    """
    GET /api/cloud/status
    Get current cloud deployment status and configuration.
    """
    try:
        config = CloudConfig()
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'cloud_config': config.to_dict(),
            'is_cloud_deployed': config.is_cloud_deployed(),
            'is_production': config.is_production()
        }), 200
    
    except Exception as e:
        logger.error(f"Cloud status error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/cloud/readiness', methods=['GET'])
def cloud_readiness():
    """
    GET /api/cloud/readiness
    Check if system is ready for cloud deployment.
    """
    try:
        readiness = CloudHealthCheck.check_cloud_readiness()
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'readiness': readiness
        }), 200
    
    except Exception as e:
        logger.error(f"Cloud readiness error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ================================================================================
# FEATURE 8: SECURITY & SYSTEM HEALTH ENDPOINTS
# ================================================================================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    GET /api/health
    System health check endpoint.
    """
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'app': current_app.config['APP_NAME'],
            'version': current_app.config['APP_VERSION'],
            'author': current_app.config['AUTHOR']
        }), 200
    
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@api_bp.route('/ready', methods=['GET'])
def ready_check():
    """
    GET /api/ready
    Kubernetes-style readiness check.
    """
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        
        return jsonify({
            'ready': True,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Readiness check error: {str(e)}")
        return jsonify({
            'ready': False,
            'error': str(e)
        }), 503
