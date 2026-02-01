"""
NeuralBrain-AI Web Views Routes
Frontend HTML and dashboard routes
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from models import db, HealthDataRecord, IngestionLog, User
from services.ingestion import DataIngestionService
from services.seed_data import DataSeeder
from services.risk_scoring import calculate_health_risk, get_risk_scorer
from services.auth_service import login_required
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
    Landing page (Public)
    """
    return render_template('public/landing.html')


@views_bp.route('/sso-callback')
def sso_callback():
    """
    GET /sso-callback
    Transition route for social login (Clerk)
    """
    return render_template('auth/sso_callback.html')


@views_bp.route('/dashboard')
@login_required
def dashboard():
    """
    GET /dashboard
    Admin Dashboard (Protected)
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
        
        # Pass user info if available in session (from login_required)
        user = session.get('user', {})
        
        return render_template('admin/dashboard.html', stats=stats, metrics_data=metrics_summary, metrics_json=json.dumps(metrics_summary), user=user)
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        db.session.rollback()
        
        # Fallback to safe defaults
        stats = {
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'sources': [],
            'latest_ingestion': None,
            'metrics_summary': {},
            'data_quality': 0
        }
        user = session.get('user', {})
        return render_template('admin/dashboard.html', stats=stats, error=str(e), metrics_json='{}', user=user)


@views_bp.route('/analytics')
@login_required
def analytics():
    """
    GET /analytics
    Analytics Dashboard with Health Metrics Charts (Protected)
    """
    try:
        metrics_summary = DataSeeder.get_health_metrics_summary()
        user = session.get('user', {})
        return render_template('admin/analytics.html', metrics_data=metrics_summary, metrics_json=json.dumps(metrics_summary), user=user)
    except Exception as e:
        logger.error(f"Error loading analytics: {str(e)}")
        user = session.get('user', {})
        return render_template('admin/analytics.html', metrics_data={}, metrics_json='{}', error=str(e), user=user)


import random

@views_bp.route('/predictions')
@login_required
def predictions():
    """
    GET /predictions
    AI Predictions Dashboard (Protected)
    """
    user = session.get('user', {})
    
    try:
        # Mock data for demonstration purposes
        dates = []
        historical_risk = []
        forecast_risk = []
        
        today = datetime.now()
        
        # specific regions data for table
        regions_risk = [
            {'region': 'Southeast Asia', 'risk_score': 78, 'trend': 'Increasing', 'status': 'High Risk'},
            {'region': 'Sub-Saharan Africa', 'risk_score': 65, 'trend': 'Stable', 'status': 'Medium Risk'},
            {'region': 'South America', 'risk_score': 92, 'trend': 'Critical', 'status': 'Outbreak Imminent'},
            {'region': 'Central Europe', 'risk_score': 12, 'trend': 'Stable', 'status': 'Low Risk'},
            {'region': 'North America', 'risk_score': 24, 'trend': 'Decreasing', 'status': 'Low Risk'},
        ]
        
        # Generate 14 days of data (7 past, 7 future)
        for i in range(7, 0, -1):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            dates.append(date)
            # Random historical fluctuation around 40-60
            historical_risk.append(random.randint(40, 65))
            forecast_risk.append(None) # Gap for chart
            
        # Today
        dates.append(today.strftime('%Y-%m-%d'))
        current_val = 62
        historical_risk.append(current_val)
        forecast_risk.append(current_val) # Connect lines
        
        # Future 7 days
        for i in range(1, 8):
            date = (today + timedelta(days=i)).strftime('%Y-%m-%d')
            dates.append(date)
            historical_risk.append(None)
            # Projected increase
            current_val += random.randint(-2, 5) 
            forecast_risk.append(min(100, max(0, current_val)))

        chart_data = {
            'dates': dates,
            'historical': historical_risk,
            'forecast': forecast_risk
        }
        
        return render_template('admin/predictions.html', user=user, chart_data=chart_data, regions=regions_risk)
        
    except Exception as e:
        logger.error(f"Error loading predictions: {str(e)}")
        # Pass empty chart_data to avoid template errors
        return render_template('admin/predictions.html', user=user, error=str(e), chart_data=None, regions=[])


@views_bp.route('/alerts')
@login_required
def alerts():
    """
    GET /alerts
    System Alerts Dashboard (Protected)
    """
    user = session.get('user', {})
    return render_template('admin/alerts.html', user=user)


@views_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """
    GET /settings
    User Settings Page (Protected)
    POST /settings
    Update user profile (including photo upload)
    """
    import os
    from werkzeug.utils import secure_filename
    
    user_data = session.get('user', {})
    
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            
            # Update database
            user_id = user_data.get('sub') or user_data.get('id')
            
            if user_id:
                user = User.query.get(user_id)
                if user:
                    user.first_name = first_name
                    user.last_name = last_name
                    
                    # Handle profile image upload
                    if 'profile_image' in request.files:
                        file = request.files['profile_image']
                        if file and file.filename:
                            # Secure the filename
                            filename = secure_filename(file.filename)
                            # Add user ID prefix for uniqueness
                            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
                            new_filename = f"{user_id}_avatar.{ext}"
                            
                            # Ensure upload directory exists
                            upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'avatars')
                            os.makedirs(upload_dir, exist_ok=True)
                            
                            # Save file
                            filepath = os.path.join(upload_dir, new_filename)
                            file.save(filepath)
                            
                            # Store relative URL in database
                            user.profile_image = f"/static/uploads/avatars/{new_filename}"
                            logger.info(f"Profile image uploaded for {user_id}: {user.profile_image}")
                    
                    db.session.commit()
                    
                    # Update session data
                    user_data['first_name'] = first_name
                    user_data['last_name'] = last_name
                    if user.profile_image:
                        user_data['profile_image'] = user.profile_image
                    session['user'] = user_data
                    
                    flash('Profile updated successfully!', 'success')
                else:
                    flash('User not found in database.', 'error')
            else:
                flash('Session error: User ID missing.', 'error')
                
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            flash(f"Error updating profile: {str(e)}", 'error')
            
        return redirect(url_for('views.settings'))

    return render_template('admin/settings.html', user=user_data)



@views_bp.route('/login')
def login():
    """Login page (Clerk)"""
    return render_template('auth/login.html')


@views_bp.route('/signup')
def signup():
    """Signup page (Clerk)"""
    return render_template('auth/signup.html')


@views_bp.route('/auth/sync', methods=['POST'])
@login_required
def auth_sync():
    """
    POST /auth/sync
    Sync user details from frontend (Clerk) to database
    """
    try:
        data = request.get_json()
        logger.info(f"Auth sync request received: {data}")
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        user_data = session.get('user', {})
        user_id = user_data.get('sub') or user_data.get('id')
        
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
            
        user = User.query.get(user_id)
        if user:
            # Update fields if provided and not already set
            email = data.get('email')
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            
            if email:
                user.email = email
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
                
            db.session.commit()
            
            # Update session as well
            user_data['email'] = email or user_data.get('email')
            user_data['first_name'] = first_name or user_data.get('first_name')
            user_data['last_name'] = last_name or user_data.get('last_name')
            session['user'] = user_data
            
            logger.info(f"User details synchronized for {user_id}")
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        logger.error(f"Auth sync error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@views_bp.route('/logout')
def logout():
    """Logout - Render logout page and clear session"""
    response = make_response(render_template('admin/logout.html'))
    # Clear the Clerk session cookie
    response.set_cookie('__session', '', expires=0)
    session.clear()
    return response



@views_bp.route('/data')
@login_required
def data_explorer():
    """
    GET /data
    Data explorer and viewer
    """
    try:
        user = session.get('user', {})
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
            'admin/data.html',
            records=paginated.items,
            paginated=paginated,
            sources=sources,
            current_source=source,
            current_status=status,
            user=user
        )
    except Exception as e:
        logger.error(f"Error loading data explorer: {str(e)}")
        user = session.get('user', {})
        return render_template('admin/data.html', error=str(e), records=[], paginated=None, user=user)


@views_bp.route('/ingest', methods=['GET', 'POST'])
@login_required
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





@views_bp.route('/contact')
def contact():
    """
    GET /contact
    Contact page - points to about page (about/contact combined)
    """
    return render_template('public/about.html')


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
    
    return render_template('public/api_docs.html', endpoints=apis)


@views_bp.route('/health-risk')
@login_required
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
        
        user = session.get('user', {})
        return render_template('admin/health_risk.html', stats=stats, user=user)
        
    except Exception as e:
        logger.error(f"Health risk dashboard error: {str(e)}")
        flash(f'Error loading health risk assessment: {str(e)}', 'danger')
        return redirect(url_for('views.index'))
