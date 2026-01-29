"""
NeuralBrain-AI Web Views Routes
Frontend HTML and dashboard routes
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, HealthDataRecord, IngestionLog
from services.ingestion import DataIngestionService
from services.seed_data import DataSeeder
from services.risk_scoring import calculate_health_risk, get_risk_scorer
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

views_bp = Blueprint('views', __name__)

ingestion_service = DataIngestionService()


@views_bp.route('/')
def index():
    """
    GET /
    Dashboard homepage with system overview and visualizations
    """
    try:
        # Get recent statistics
        total_records = HealthDataRecord.query.count()
        valid_records = HealthDataRecord.query.filter_by(status='valid').count()
        invalid_records = HealthDataRecord.query.filter_by(status='invalid').count()
        
        # Get latest ingestion log
        latest_log = IngestionLog.query.order_by(IngestionLog.timestamp.desc()).first()
        
        # Get data sources
        sources = db.session.query(HealthDataRecord.data_source).distinct().all()
        sources = [s[0] for s in sources]
        
        # Get health metrics summary for visualization
        metrics_summary = DataSeeder.get_health_metrics_summary()
        
        stats = {
            'total_records': total_records,
            'valid_records': valid_records,
            'invalid_records': invalid_records,
            'sources': sources,
            'latest_ingestion': latest_log.to_dict() if latest_log else None,
            'metrics_summary': metrics_summary,
            'data_quality': (valid_records / (valid_records + invalid_records) * 100) if (valid_records + invalid_records) > 0 else 0
        }
        
        return render_template('dashboard_new.html', stats=stats, metrics_data=metrics_summary, metrics_json=json.dumps(metrics_summary))
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        return render_template('dashboard.html', stats={}, error=str(e), metrics_json='{}')


@views_bp.route('/data')
def data_explorer():
    """
    GET /data
    Data explorer and viewer
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        query = HealthDataRecord.query.order_by(HealthDataRecord.timestamp.desc())
        
        # Apply filters
        source = request.args.get('source', type=str)
        status = request.args.get('status', type=str)
        
        if source:
            query = query.filter_by(data_source=source)
        if status:
            query = query.filter_by(status=status)
        
        paginated = query.paginate(page=page, per_page=per_page)
        
        # Get available sources for filter
        sources = db.session.query(HealthDataRecord.data_source).distinct().all()
        sources = [s[0] for s in sources]
        
        return render_template(
            'data.html',
            records=paginated.items,
            paginated=paginated,
            sources=sources,
            current_source=source,
            current_status=status
        )
    except Exception as e:
        logger.error(f"Error loading data explorer: {str(e)}")
        return render_template('data.html', error=str(e), records=[], paginated=None)


@views_bp.route('/ingest', methods=['GET', 'POST'])
def trigger_ingest():
    """
    POST /ingest
    Trigger manual data ingestion
    """
    if request.method == 'POST':
        try:
            logger.info("Manual ingestion triggered")
            result = ingestion_service.ingest_all_sources()
            
            if result['successful'] > 0:
                flash(f"✓ Ingestion complete: {result['successful']} source(s) succeeded", 'success')
            else:
                flash(f"✗ Ingestion failed: all sources failed", 'warning')
            
            return redirect(url_for('views.index'))
        except Exception as e:
            logger.error(f"Ingestion error: {str(e)}")
            flash(f"✗ Ingestion error: {str(e)}", 'error')
            return redirect(url_for('views.index'))
    
    return redirect(url_for('views.index'))


@views_bp.route('/about')
def about():
    """
    GET /about
    About page with project information
    """
    return render_template('about.html')


@views_bp.route('/contact')
def contact():
    """
    GET /contact
    Contact page - points to about page (about/contact combined)
    """
    return render_template('about.html')


@views_bp.route('/api-docs')
def api_docs():
    """
    GET /api-docs
    API documentation page
    """
    apis = {
        'GET /api/status': 'Get system status and available endpoints',
        'GET /api/health': 'Health check endpoint',
        'POST /api/ingest': 'Trigger data ingestion from all sources',
        'GET /api/data': 'Get normalized health data (supports filtering and pagination)',
        'GET /api/data/<id>': 'Get specific record by ID',
        'GET /api/logs': 'Get ingestion operation logs',
        'POST /api/validate': 'Validate health data against rules',
    }
    
    return render_template('api_docs.html', endpoints=apis)


@views_bp.route('/health-risk')
def health_risk():
    """
    GET /health-risk
    AI-Based Health Risk Assessment Dashboard
    Shows risk scores, trends, and personalized recommendations
    """
    try:
        records = HealthDataRecord.query.order_by(HealthDataRecord.timestamp).all()
        
        if not records:
            flash('No health records available for risk assessment', 'warning')
            return redirect(url_for('views.index'))
        
        # Get risk assessment for latest record
        latest_risk = calculate_health_risk(records, -1)
        
        # Get historical risk data (last 30 records)
        recent_records = records[-30:] if len(records) > 30 else records
        risk_history = []
        
        for idx, record in enumerate(recent_records):
            risk = calculate_health_risk(records, len(records) - len(recent_records) + idx)
            risk_history.append({
                'timestamp': record.timestamp.isoformat(),
                'risk_level': risk['overall_risk'],
                'risk_score': risk['risk_percentage']
            })
        
        # Get model info
        scorer = get_risk_scorer()
        
        stats = {
            'total_records': len(records),
            'ml_trained': scorer.ml_detector.is_trained,
            'latest_risk': latest_risk,
            'risk_history': risk_history
        }
        
        return render_template('health_risk.html', stats=stats)
        
    except Exception as e:
        logger.error(f"Health risk dashboard error: {str(e)}")
        flash(f'Error loading health risk assessment: {str(e)}', 'danger')
        return redirect(url_for('views.index'))
