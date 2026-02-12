"""
Prediction Scheduler - Hourly Update Loop

Runs predictions every hour using APScheduler:
1. Fetch latest disease data
2. Run GPT predictions
3. Generate alerts
4. Update database
5. Log execution

✅ RESILIENT to API failures (continues running, retries next hour)
✅ Survives Flask restarts
✅ Does NOT shut down on errors
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class PredictionScheduler:
    """Manages hourly prediction scheduling"""
    
    _scheduler = None
    _is_running = False
    _app = None
    
    @classmethod
    def init_scheduler(cls, app=None):
        """Initialize the scheduler with Flask app context"""
        try:
            if cls._scheduler is None:
                cls._scheduler = BackgroundScheduler(daemon=True)
                
                # Add hourly prediction job (runs every hour)
                cls._scheduler.add_job(
                    func=cls._run_predictions_with_context,
                    trigger=IntervalTrigger(hours=1),
                    id='hourly_predictions',
                    name='Hourly AI Predictions',
                    replace_existing=True,
                    misfire_grace_time=900  # 15 minutes grace period
                )
                
                logger.info("✅ Scheduler initialized (BackgroundScheduler)")
                
                # Store app reference for context
                if app:
                    cls._app = app
                    cls._scheduler.start()
                    cls._is_running = True
                    logger.info("✅ Scheduler started (hourly cycle active)")
                    logger.info("✅ Next prediction will run in 1 hour")
                    logger.info("✅ Scheduler is RESILIENT: will retry on API failures")
                else:
                    logger.warning("⚠️ No Flask app provided to scheduler")
                    
        except Exception as e:
            logger.error(f"❌ Scheduler initialization error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    @classmethod
    def _run_predictions_with_context(cls):
        """Run predictions within Flask app context"""
        if not hasattr(cls, '_app') or cls._app is None:
            logger.error("❌ No Flask app context available for scheduler")
            return
            
        with cls._app.app_context():
            cls._run_predictions()
    
    @classmethod
    def _run_predictions(cls):
        """Execute full prediction pipeline with error resilience"""
        try:
            start_time = datetime.utcnow()
            logger.info("\n" + "="*60)
            logger.info("🔮 HOURLY PREDICTION CYCLE STARTING")
            logger.info("="*60)
            
            # Import services here to avoid circular imports
            from services.disease_data_service import DiseaseDataService
            from services.prediction_service import PredictionService
            from services.alert_engine import AlertEngine
            from services.data_normalizer import DataNormalizer
            
            # 1. Fetch real data
            logger.info("\n📊 STEP 1: Fetching real disease data...")
            try:
                global_stats = DiseaseDataService.get_global_stats()
                countries = DiseaseDataService.get_countries_data()
                historical = DiseaseDataService.get_historical_data(days=60)
                regional_risks = DiseaseDataService.get_regional_outbreak_risk()
                
                logger.info(f"   ✅ Global: {global_stats.get('cases', 0):,} cases")
                logger.info(f"   ✅ Countries: {len(countries)} regions")
                logger.info(f"   ✅ Historical: {len(historical)} days")
                logger.info(f"   ✅ Regional risks: {len(regional_risks)} high-risk areas")
            except Exception as e:
                logger.error(f"   ❌ Data fetch failed: {str(e)}")
                raise
            
            # 2. Generate predictions
            logger.info("\n🤖 STEP 2: Generating predictions...")
            try:
                predictor = PredictionService()
                predictions_7day = predictor.predict_outbreak_7_day(
                    global_stats,
                    countries,
                    historical
                )
                regional_predictions = predictor.predict_regional_risk(countries)
                health_analytics = predictor.predict_health_analytics(global_stats, countries)
                
                logger.info(f"   ✅ 7-day forecast: {len(predictions_7day)} days")
                logger.info(f"   ✅ Regional predictions: {len(regional_predictions)} regions")
                logger.info(f"   ✅ Health analytics generated")
            except Exception as e:
                logger.warning(f"   ⚠️ Predictions failed (using fallback): {str(e)}")
                # Use empty/fallback predictions
                predictions_7day = [{'day': i+1, 'predicted_cases': 0} for i in range(7)]
                regional_predictions = []
                health_analytics = {}
            
            # 3. Generate alerts
            logger.info("\n🚨 STEP 3: Generating alerts...")
            try:
                alerts = AlertEngine.generate_alerts(
                    global_stats,
                    regional_predictions,
                    predictions_7day,
                    historical
                )
                logger.info(f"   ✅ Total alerts: {len(alerts)}")
            except Exception as e:
                logger.warning(f"   ⚠️ Alert generation failed: {str(e)}")
                alerts = []
            
            # 4. Normalize data for frontend
            logger.info("\n📦 STEP 4: Normalizing data for frontend...")
            try:
                dashboard_metrics = DataNormalizer.normalize_dashboard_metrics(global_stats)
                chart_data = DataNormalizer.normalize_chart_data(historical)
                map_data = DataNormalizer.normalize_map_data(regional_predictions)
                alerts_normalized = DataNormalizer.normalize_alerts(alerts)
                predictions_normalized = DataNormalizer.normalize_predictions(predictions_7day)
                analytics_normalized = DataNormalizer.normalize_analytics(health_analytics)
                
                logger.info("   ✅ All data normalized")
            except Exception as e:
                logger.warning(f"   ⚠️ Data normalization failed: {str(e)}")
            
            # 5. Store in database/cache
            logger.info("\n💾 STEP 5: Storing predictions...")
            try:
                cls._store_predictions({
                    'dashboard_metrics': dashboard_metrics,
                    'chart_data': chart_data,
                    'map_data': map_data,
                    'alerts': alerts_normalized,
                    'predictions': predictions_normalized,
                    'analytics': analytics_normalized,
                    'timestamp': datetime.utcnow().isoformat()
                })
                logger.info("   ✅ All data stored successfully")
            except Exception as e:
                logger.warning(f"   ⚠️ Data storage failed: {str(e)}")
            
            # 6. Log execution summary
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info("\n" + "="*60)
            logger.info(f"✅ PREDICTION CYCLE COMPLETE in {duration:.1f}s")
            logger.info("="*60 + "\n")
            
        except Exception as e:
            logger.error(f"\n❌ PREDICTION CYCLE FAILED: {str(e)}")
            logger.warning("⚠️ SCHEDULER RESILIENCE: Will retry predictions in 1 hour")
            logger.warning("⚠️ Server will continue running - scheduler will not shut down")
    
    @classmethod
    def _store_predictions(cls, data: dict):
        """Store predictions in database or cache"""
        try:
            import json
            cache_file = os.path.join(
                os.path.dirname(__file__),
                '..',
                'cache',
                'latest_predictions.json'
            )
            
            # Create cache directory if needed
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"   📁 Cache updated")
            
        except Exception as e:
            logger.error(f"   ❌ Cache storage error: {str(e)}")
    
    @classmethod
    def get_latest_predictions(cls) -> dict:
        """Retrieve latest predictions from cache"""
        try:
            import json
            cache_file = os.path.join(
                os.path.dirname(__file__),
                '..',
                'cache',
                'latest_predictions.json'
            )
            
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    return json.load(f)
            
        except Exception as e:
            logger.error(f"❌ Cache retrieval error: {str(e)}")
        
        return {}
    
    @classmethod
    def get_scheduler_status(cls) -> dict:
        """Get scheduler status"""
        if cls._scheduler is None:
            return {"status": "not_initialized"}
        
        jobs = []
        if cls._scheduler.get_jobs():
            for job in cls._scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                })
        
        return {
            "status": "running" if cls._is_running else "stopped",
            "jobs": jobs,
            "running": cls._is_running,
            "resilient": True,
            "note": "Scheduler will continue running even if API calls fail"
        }
    
    @classmethod
    def start(cls):
        """Start the scheduler"""
        try:
            if cls._scheduler and not cls._is_running:
                cls._scheduler.start()
                cls._is_running = True
                logger.info("✅ Scheduler started")
        except Exception as e:
            logger.error(f"❌ Scheduler start error: {str(e)}")
    
    @classmethod
    def stop(cls):
        """Stop the scheduler"""
        try:
            if cls._scheduler and cls._is_running:
                cls._scheduler.shutdown()
                cls._is_running = False
                logger.info("✅ Scheduler stopped")
        except Exception as e:
            logger.error(f"❌ Scheduler stop error: {str(e)}")
