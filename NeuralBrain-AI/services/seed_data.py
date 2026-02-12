"""
Seed Data Service
Generates sample health data for demonstration and testing

Uses Huawei Cloud health metrics inference when available,
falls back to random generation if cloud unavailable.
"""

import random
import logging
from datetime import datetime, timedelta
from models import db, HealthDataRecord

logger = logging.getLogger(__name__)

# Import AI services adapter
try:
    from ai_services.inference_adapter import get_health_metrics_adapter
    AI_SERVICES_AVAILABLE = True
except ImportError:
    AI_SERVICES_AVAILABLE = False
    logger.warning("AI Services not available, using fallback health metrics")


class DataSeeder:
    """
    Generates realistic sample health data for visualization and testing.
    """
    
    # Sample health metrics data
    SAMPLE_SOURCES = ['covid19', 'heart_rate', 'epidemiological']
    
    # Health metric ranges (realistic values)
    METRIC_RANGES = {
        'heart_rate': {'min': 60, 'max': 100, 'unit': 'bpm'},
        'temperature': {'min': 36.5, 'max': 37.5, 'unit': 'C'},
        'blood_pressure_sys': {'min': 110, 'max': 130, 'unit': 'mmHg'},
        'blood_pressure_dia': {'min': 70, 'max': 85, 'unit': 'mmHg'},
        'oxygen_saturation': {'min': 95, 'max': 100, 'unit': '%'},
        'respiratory_rate': {'min': 12, 'max': 16, 'unit': 'breaths/min'},
        'glucose_level': {'min': 70, 'max': 100, 'unit': 'mg/dL'},
    }
    
    @staticmethod
    def generate_sample_metrics():
        """
        Generate realistic health metrics.
        
        Uses Huawei Cloud ModelArts if available, falls back to random generation.
        """
        if AI_SERVICES_AVAILABLE:
            try:
                adapter = get_health_metrics_adapter()
                metrics = adapter.get_health_metrics(
                    patient_id="seed-data",
                    context="daily_monitoring",
                    fallback_fn=DataSeeder._generate_random_metrics
                )
                return metrics
            except Exception as e:
                logger.debug(f"AI Services health metrics failed, using fallback: {str(e)}")
                return DataSeeder._generate_random_metrics()
        else:
            return DataSeeder._generate_random_metrics()
    
    @staticmethod
    def _generate_random_metrics():
        """Fallback: Generate random health metrics locally."""
        return {
            'heart_rate': random.randint(60, 100),
            'temperature': round(random.uniform(36.5, 37.5), 1),
            'blood_pressure_sys': random.randint(110, 130),
            'blood_pressure_dia': random.randint(70, 85),
            'oxygen_saturation': random.randint(95, 100),
            'respiratory_rate': random.randint(12, 16),
            'glucose_level': random.randint(70, 100),
            'bmi': round(random.uniform(18.5, 25), 1),
            'activity_level': random.choice(['low', 'moderate', 'high']),
        }
    
    @staticmethod
    def generate_covid_metrics():
        """Generate COVID-19 epidemiological data."""
        return {
            'case_count': random.randint(1000, 50000),
            'death_count': random.randint(10, 500),
            'recovery_count': random.randint(500, 30000),
            'daily_cases': random.randint(100, 5000),
            'daily_deaths': random.randint(5, 200),
            'country': random.choice(['United States', 'United Kingdom', 'Canada', 'Germany', 'France']),
            'last_update': datetime.utcnow().isoformat(),
        }
    
    @classmethod
    def seed_health_records(cls, count=50):
        """
        Generate and insert sample health data records.
        
        Args:
            count: Number of records to generate (default: 50)
            
        Returns:
            Number of records created
        """
        try:
            logger.info(f"Seeding {count} health data records...")
            
            created_count = 0
            
            # Generate records from different sources and time periods
            for i in range(count):
                # Vary timestamps over the last 7 days
                days_back = random.randint(0, 7)
                hours_back = random.randint(0, 23)
                timestamp = datetime.utcnow() - timedelta(days=days_back, hours=hours_back)
                
                # Randomly choose data source
                source = random.choice(cls.SAMPLE_SOURCES)
                
                if source == 'covid19' or source == 'epidemiological':
                    # COVID-19 epidemiological data
                    processed_data = cls.generate_covid_metrics()
                    raw_data = processed_data.copy()
                else:
                    # Personal health metrics
                    processed_data = cls.generate_sample_metrics()
                    raw_data = processed_data.copy()
                
                # Create record
                record = HealthDataRecord(
                    data_source=source,
                    raw_data=raw_data,
                    processed_data=processed_data,
                    metrics=processed_data,
                    timestamp=timestamp,
                    status='valid',
                    validation_notes=f'Seeded sample data for {source}'
                )
                
                db.session.add(record)
                created_count += 1
            
            # Commit all records
            db.session.commit()
            logger.info(f"✓ Successfully seeded {created_count} records")
            return created_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error seeding data: {str(e)}")
            return 0
    
    @classmethod
    def clear_data(cls):
        """
        Clear all health data records (for testing).
        
        Returns:
            Number of records deleted
        """
        try:
            count = HealthDataRecord.query.delete()
            db.session.commit()
            logger.info(f"Cleared {count} records")
            return count
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error clearing data: {str(e)}")
            return 0
    
    @classmethod
    def get_statistics(cls):
        """
        Get statistics about the seeded data.
        
        Returns:
            Dictionary with data statistics
        """
        total_records = HealthDataRecord.query.count()
        valid_records = HealthDataRecord.query.filter_by(status='valid').count()
        invalid_records = HealthDataRecord.query.filter_by(status='invalid').count()
        
        sources = {}
        for record in HealthDataRecord.query.all():
            if record.data_source not in sources:
                sources[record.data_source] = 0
            sources[record.data_source] += 1
        
        return {
            'total_records': total_records,
            'valid_records': valid_records,
            'invalid_records': invalid_records,
            'sources': sources
        }
    
    @classmethod
    def get_health_metrics_summary(cls):
        """
        Get aggregated health metrics from all records.
        
        Returns:
            Dictionary with average values for health metrics
        """
        records = HealthDataRecord.query.filter_by(status='valid').all()
        
        if not records:
            return {}
        
        # Initialize aggregates
        aggregates = {
            'heart_rate': [],
            'temperature': [],
            'blood_pressure_sys': [],
            'blood_pressure_dia': [],
            'oxygen_saturation': [],
            'respiratory_rate': [],
            'glucose_level': [],
            'bmi': [],
        }
        
        # Collect values
        for record in records:
            metrics = record.metrics or {}
            for metric in aggregates.keys():
                if metric in metrics and isinstance(metrics[metric], (int, float)):
                    aggregates[metric].append(metrics[metric])
        
        # Calculate averages
        summary = {}
        for metric, values in aggregates.items():
            if values:
                summary[metric] = {
                    'average': round(sum(values) / len(values), 2),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values),
                    'unit': cls.METRIC_RANGES.get(metric, {}).get('unit', '')
                }
        
        return summary
