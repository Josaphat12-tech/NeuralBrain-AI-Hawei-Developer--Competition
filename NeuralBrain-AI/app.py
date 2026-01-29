"""
NeuralBrain-AI - Zero-Cost Health Monitoring Platform
Main application entry point

Developed by: Bitingo Josaphat JB
Version: 1.0.0
Year: 2026

This is the production-ready entry point for the NeuralBrain-AI platform.
The system is designed for zero-cost operation using only free public APIs.
"""

import os
import logging
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name='config'):
    """
    Application factory function.
    
    Args:
        config_name: Name of config module (default: 'config')
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Load configuration
    app.config.from_object(config_name)
    
    # Initialize database
    from models import db
    db.init_app(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("Database initialized")
        
        # Seed sample data if database is empty
        from models import HealthDataRecord
        if HealthDataRecord.query.count() == 0:
            from services.seed_data import DataSeeder
            DataSeeder.seed_health_records(count=50)
            logger.info("Sample data seeded successfully")
        
        # Initialize AI risk scorer with training
        try:
            from services.risk_scoring import get_risk_scorer
            scorer = get_risk_scorer()
            records = HealthDataRecord.query.all()
            if len(records) >= 20:
                scorer.train_on_history(records)
                logger.info("✓ AI Risk Scorer trained on historical data")
            else:
                logger.info("⏳ AI Risk Scorer ready (requires 20+ records for full training)")
        except Exception as e:
            logger.warning(f"AI Risk Scorer initialization: {str(e)}")
    
    # Register blueprints
    from routes.api import api_bp
    from routes.views import views_bp
    
    app.register_blueprint(api_bp)
    app.register_blueprint(views_bp)
    
    logger.info("Blueprints registered: api, views")
    
    # Register error handlers
    register_error_handlers(app)
    
    # Add security headers to all responses
    @app.after_request
    def add_security_headers(response):
        from services.security import SecurityHeaders
        headers = SecurityHeaders.get_security_headers()
        for header, value in headers.items():
            response.headers[header] = value
        # Attribution header
        response.headers['X-Powered-By'] = 'NeuralBrain-AI by Bitingo Josaphat JB'
        return response
    
    # Initialize offline support
    @app.before_request
    def init_offline_support():
        from services.offline import get_cache_manager, get_connection_status
        get_cache_manager()
        get_connection_status()
    
    # Initialize alert system
    @app.before_request
    def init_alert_system():
        from services.alerts import get_alert_manager
        get_alert_manager()
    
    logger.info("✅ Security headers configured")
    logger.info("✅ Offline-first support initialized")
    logger.info("✅ Alert system initialized")
    
    # Register context processors
    register_context_processors(app)
    
    # Log startup information
    logger.info(f"=== NeuralBrain-AI {app.config['APP_VERSION']} ===")
    logger.info(f"Author: {app.config['AUTHOR']}")
    logger.info(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    logger.info("Application ready for requests")
    
    return app


def register_error_handlers(app):
    """
    Register custom error handlers for the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"Internal server error: {str(error)}")
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 errors."""
        return render_template('errors/403.html'), 403


def register_context_processors(app):
    """
    Register context processors for template rendering.
    
    Args:
        app: Flask application instance
    """
    
    @app.context_processor
    def inject_config():
        """Inject configuration into template context."""
        return {
            'config': app.config,
            'author': app.config['AUTHOR'],
            'app_name': app.config['APP_NAME'],
            'app_version': app.config['APP_VERSION']
        }


if __name__ == '__main__':
    # Create application
    app = create_app()
    
    # Determine debug mode
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    port = int(os.getenv('FLASK_PORT', 5000))
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    
    # Run development server
    logger.info(f"Starting Flask development server on {host}:{port} (debug={debug_mode})")
    logger.info("Access the application at http://localhost:5000")
    
    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        use_reloader=False,
        threaded=True
    )
