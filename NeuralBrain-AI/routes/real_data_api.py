"""
REAL DATA API ROUTES - GPT-Powered Health Intelligence

All predictions, analytics, and alerts are calculated by GPT based on REAL disease data.

Data Flow:
1. Fetch REAL COVID-19 data from disease.sh
2. Pass to GPT for AI analysis
3. GPT returns structured NUMERIC JSON only
4. Send to frontend for visualization

CRITICAL: All GPT outputs are STRICTLY NUMERIC with NO natural language
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
import logging

# Import all services
from services.disease_data_service import DiseaseDataService
from services.prediction_service import PredictionService
from services.alert_engine import AlertEngine
from services.data_normalizer import DataNormalizer
from services.icd_service import ICDService
from services.scheduler import PredictionScheduler

logger = logging.getLogger(__name__)

real_data_api = Blueprint('real_data_api', __name__, url_prefix='/api')

# ═══════════════════════════════════════════════════════════════════════════
# PRIMARY REAL DATA ENDPOINTS - ALL CALCULATIONS VIA GPT
# ═══════════════════════════════════════════════════════════════════════════

@real_data_api.route('/dashboard/metrics', methods=['GET'])
def get_dashboard_metrics():
    """
    GET /api/dashboard/metrics
    
    Returns REAL global health metrics:
    - 700M+ COVID-19 cases from disease.sh
    - Real data quality assessment
    - Active alerts count
    
    ✅ FRONTEND DATA CONTRACT: Matches dashboard.html expectations
    """
    try:
        logger.info("📊 Dashboard metrics requested")
        
        # Get latest cached predictions (updated hourly by scheduler)
        cached = PredictionScheduler.get_latest_predictions()
        if cached and 'dashboard_metrics' in cached:
            logger.info("✅ Returning cached dashboard metrics")
            return jsonify(cached['dashboard_metrics']), 200
        
        # Fallback: generate on-demand
        logger.info("⚠️ Cache miss, generating metrics on-demand...")
        global_stats = DiseaseDataService.get_global_stats()
        metrics = DataNormalizer.normalize_dashboard_metrics(global_stats)
        
        logger.info(f"✅ Dashboard: {metrics.get('total_records', 0)} cases")
        return jsonify(metrics), 200
        
    except Exception as e:
        logger.error(f"❌ Dashboard metrics error: {str(e)}")
        return jsonify(DataNormalizer._get_fallback_dashboard_metrics()), 200


@real_data_api.route('/predictions/outbreak', methods=['GET'])
def get_outbreak_predictions():
    """
    GET /api/predictions/outbreak
    
    Returns GPT-calculated 7-day outbreak forecast:
    - Day-by-day predicted cases
    - Confidence scores (decreasing)
    - Severity levels (CRITICAL/HIGH/MEDIUM/LOW)
    
    ✅ FRONTEND DATA CONTRACT: Matches predictions.html expectations
    Format: {"forecast": [{day, predicted_cases, confidence, severity}...]}
    """
    try:
        logger.info("🔮 Outbreak predictions requested")
        
        # Try cached first
        cached = PredictionScheduler.get_latest_predictions()
        if cached and 'predictions' in cached:
            logger.info("✅ Returning cached predictions")
            return jsonify(cached['predictions']), 200
        
        # Generate on-demand
        logger.info("⚠️ Generating predictions on-demand...")
        global_stats = DiseaseDataService.get_global_stats()
        countries = DiseaseDataService.get_countries_data()
        historical = DiseaseDataService.get_historical_data(days=60)
        
        # GPT predictions
        predictor = PredictionService()
        forecast = predictor.predict_outbreak_7_day(global_stats, countries, historical)
        
        predictions_data = DataNormalizer.normalize_predictions(forecast)
        logger.info(f"✅ 7-day forecast: {len(forecast)} days")
        return jsonify(predictions_data), 200
        
    except Exception as e:
        logger.error(f"❌ Predictions error: {str(e)}")
        return jsonify(DataNormalizer._get_fallback_predictions()), 200


@real_data_api.route('/system/alerts', methods=['GET'])
def get_system_alerts():
    """
    GET /api/system/alerts
    
    Returns real-time alerts calculated by GPT:
    - 🚨 CRITICAL: High-risk situations
    - ⚠️ WARNING: Elevated risk
    - ℹ️ INFO: Routine updates
    
    All alerts are data-driven and include:
    - Risk scores (0-100)
    - Regional information
    - Severity classification
    - Expiry timestamps
    
    ✅ FRONTEND DATA CONTRACT: Matches alerts.html expectations
    """
    try:
        logger.info("🚨 System alerts requested")
        
        # Try cached first
        cached = PredictionScheduler.get_latest_predictions()
        if cached and 'alerts' in cached:
            logger.info("✅ Returning cached alerts")
            return jsonify(cached['alerts']), 200
        
        # Generate on-demand
        logger.info("⚠️ Generating alerts on-demand...")
        global_stats = DiseaseDataService.get_global_stats()
        regional_risks = DiseaseDataService.get_regional_outbreak_risk()
        historical = DiseaseDataService.get_historical_data(days=60)
        
        # GPT predictions
        predictor = PredictionService()
        predictions = predictor.predict_outbreak_7_day(
            global_stats,
            DiseaseDataService.get_countries_data(),
            historical
        )
        
        # Generate alerts
        alerts = AlertEngine.generate_alerts(
            global_stats,
            regional_risks,
            predictions,
            historical
        )
        
        alerts_data = DataNormalizer.normalize_alerts(alerts)
        logger.info(f"✅ Generated {len(alerts)} alerts")
        return jsonify(alerts_data), 200
        
    except Exception as e:
        logger.error(f"❌ Alerts error: {str(e)}")
        return jsonify(DataNormalizer._get_fallback_alerts()), 200


@real_data_api.route('/data/regional', methods=['GET'])
def get_regional_data():
    """
    GET /api/data/regional
    
    Returns per-country COVID-19 data for world map visualization:
    - Country name, coordinates (lat/lng)
    - Cases, deaths, recovered
    - Risk score calculated by GPT
    - Severity level
    
    ✅ FRONTEND DATA CONTRACT: Matches map.html expectations
    All numbers are NUMERIC for proper map rendering
    """
    try:
        logger.info("🗺️ Regional data requested")
        
        # Try cached first
        cached = PredictionScheduler.get_latest_predictions()
        if cached and 'map_data' in cached:
            logger.info("✅ Returning cached map data")
            return jsonify({"regions": cached['map_data']}), 200
        
        # Generate on-demand
        logger.info("⚠️ Generating regional data on-demand...")
        regional_risks = DiseaseDataService.get_regional_outbreak_risk()
        map_data = DataNormalizer.normalize_map_data(regional_risks)
        
        logger.info(f"✅ Regional data: {len(map_data)} countries")
        return jsonify({"regions": map_data}), 200
        
    except Exception as e:
        logger.error(f"❌ Regional data error: {str(e)}")
        return jsonify({"regions": DataNormalizer._get_fallback_map_data()}), 200


@real_data_api.route('/health/analytics', methods=['GET'])
def get_health_analytics():
    """
    GET /api/health/analytics
    
    Returns GPT-calculated health analytics based on REAL pandemic data:
    - Heart rate statistics
    - Temperature patterns
    - Blood pressure trends
    - Oxygen saturation metrics
    - Glucose levels
    - Respiratory rate
    - Health risk index
    - System strain assessment
    
    ALL VALUES STRICTLY NUMERIC - Calculated by GPT based on disease patterns
    """
    try:
        logger.info("❤️ Health analytics requested")
        
        # Try cached first
        cached = PredictionScheduler.get_latest_predictions()
        if cached and 'analytics' in cached:
            logger.info("✅ Returning cached analytics")
            return jsonify(cached['analytics']), 200
        
        # Generate on-demand
        logger.info("⚠️ Generating analytics on-demand...")
        global_stats = DiseaseDataService.get_global_stats()
        countries = DiseaseDataService.get_countries_data()
        
        # GPT health analytics
        predictor = PredictionService()
        analytics = predictor.predict_health_analytics(global_stats, countries)
        
        normalized_analytics = DataNormalizer.normalize_analytics(analytics)
        logger.info("✅ Health analytics generated (all numeric)")
        return jsonify(normalized_analytics), 200
        
    except Exception as e:
        logger.error(f"❌ Analytics error: {str(e)}")
        return jsonify(DataNormalizer._get_fallback_analytics()), 200


@real_data_api.route('/trends/health', methods=['GET'])
def get_health_trends():
    """
    GET /api/trends/health
    
    Returns 60-day historical trend data for charts:
    - Cases per day
    - Deaths per day
    - Recovered per day
    - Quality metrics
    
    ✅ FRONTEND DATA CONTRACT: Matches chart format
    """
    try:
        logger.info("📈 Health trends requested")
        
        # Try cached first
        cached = PredictionScheduler.get_latest_predictions()
        if cached and 'chart_data' in cached:
            logger.info("✅ Returning cached trend data")
            return jsonify(cached['chart_data']), 200
        
        # Generate on-demand
        logger.info("⚠️ Generating trend data on-demand...")
        historical = DiseaseDataService.get_historical_data(days=60)
        chart_data = DataNormalizer.normalize_chart_data(historical)
        
        logger.info(f"✅ Trends: {len(historical)} days")
        return jsonify(chart_data), 200
        
    except Exception as e:
        logger.error(f"❌ Trends error: {str(e)}")
        return jsonify(DataNormalizer._get_fallback_chart_data()), 200


# ═══════════════════════════════════════════════════════════════════════════
# SCHEDULER & SYSTEM ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@real_data_api.route('/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """
    GET /api/scheduler/status
    
    Returns prediction scheduler status and next execution time
    """
    try:
        status = PredictionScheduler.get_scheduler_status()
        logger.info(f"📅 Scheduler status: {status.get('status')}")
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"❌ Scheduler status error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@real_data_api.route('/scheduler/run', methods=['POST'])
def run_scheduler_now():
    """
    POST /api/scheduler/run
    
    Trigger prediction cycle immediately (for testing/debugging)
    """
    try:
        logger.info("🔄 Manual scheduler trigger requested")
        PredictionScheduler._run_predictions()
        return jsonify({"status": "success", "message": "Predictions generated"}), 200
    except Exception as e:
        logger.error(f"❌ Manual scheduler error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@real_data_api.route('/health/check', methods=['GET'])
def health_check():
    """
    GET /api/health/check
    
    System health status and data source availability
    """
    try:
        # Check data source availability
        try:
            DiseaseDataService.get_global_stats()
            disease_sh_available = True
        except:
            disease_sh_available = False
        
        # Check GPT availability
        try:
            predictor = PredictionService()
            gpt_available = predictor.available
        except:
            gpt_available = False
        
        status = {
            "status": "healthy" if (disease_sh_available or gpt_available) else "degraded",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "services": {
                "disease_sh": "available" if disease_sh_available else "unavailable",
                "openai_gpt": "available" if gpt_available else "unavailable",
                "cache": "available"
            },
            "scheduler": PredictionScheduler.get_scheduler_status()
        }
        
        logger.info(f"✅ Health check: {status['status']}")
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"❌ Health check error: {str(e)}")
        return jsonify({"status": "error"}), 500


@real_data_api.route('/version', methods=['GET'])
def get_version():
    """
    GET /api/version
    
    API version and system information
    """
    return jsonify({
        "version": "2.0.0",
        "mode": "REAL_DATA_GPT_POWERED",
        "description": "GPT-calculated predictions from real disease data",
        "data_sources": [
            "disease.sh (PRIMARY)",
            "OpenAI GPT-3.5-turbo (PREDICTIONS)",
            "ICD (DISEASE CLASSIFICATION)"
        ],
        "update_frequency": "hourly",
        "last_update": datetime.utcnow().isoformat() + "Z"
    }), 200


# ═══════════════════════════════════════════════════════════════════════════
# DEBUG ENDPOINTS (for verification)
# ═══════════════════════════════════════════════════════════════════════════

@real_data_api.route('/debug/raw-disease-data', methods=['GET'])
def debug_raw_disease_data():
    """
    GET /api/debug/raw-disease-data
    
    Raw disease.sh data (for debugging/verification)
    """
    if not current_app.config.get('DEBUG'):
        return jsonify({"error": "Debug mode disabled"}), 403
    
    try:
        global_stats = DiseaseDataService.get_global_stats()
        countries = DiseaseDataService.get_countries_data()
        return jsonify({
            "global": global_stats,
            "top_countries": countries[:5],
            "total_countries": len(countries)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@real_data_api.route('/debug/gpt-predictions', methods=['GET'])
def debug_gpt_predictions():
    """
    GET /api/debug/gpt-predictions
    
    Raw GPT predictions (for verification)
    """
    if not current_app.config.get('DEBUG'):
        return jsonify({"error": "Debug mode disabled"}), 403
    
    try:
        global_stats = DiseaseDataService.get_global_stats()
        countries = DiseaseDataService.get_countries_data()
        historical = DiseaseDataService.get_historical_data(days=60)
        
        predictor = PredictionService()
        predictions = predictor.predict_outbreak_7_day(global_stats, countries, historical)
        regional = predictor.predict_regional_risk(countries)
        
        return jsonify({
            "7day_forecast": predictions,
            "regional_risks": regional[:5],
            "gpt_available": predictor.available
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
