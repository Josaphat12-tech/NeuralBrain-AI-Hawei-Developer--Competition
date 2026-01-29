"""
Data Normalization Service
Transforms and standardizes health data from multiple sources
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DataNormalizer:
    """
    Normalizes health data from different API sources into a consistent format.
    
    Features:
    - Field mapping
    - Unit conversion
    - Data type standardization
    - Null handling
    """
    
    # Field mapping from different API sources
    FIELD_MAPPINGS = {
        'covid19': {
            # Maps COVID-19 API fields to standard metrics
            'cases': 'case_count',
            'deaths': 'death_count',
            'recovered': 'recovery_count',
            'todayCases': 'daily_cases',
            'todayDeaths': 'daily_deaths',
        },
        'heart_rate': {
            # Maps heart rate API fields
            'id': 'user_id',
            'firstname': 'first_name',
            'lastname': 'last_name',
        }
    }
    
    def __init__(self):
        """Initialize the normalizer."""
        pass
    
    def normalize_covid_data(self, data: Dict) -> Dict:
        """
        Normalize COVID-19 epidemiological data.
        
        Args:
            data: Raw COVID-19 data from API
            
        Returns:
            Normalized dictionary
        """
        normalized = {}
        
        for source_field, target_field in self.FIELD_MAPPINGS.get('covid19', {}).items():
            if source_field in data:
                normalized[target_field] = data[source_field]
        
        # Add standardized fields
        normalized['data_type'] = 'epidemiological'
        normalized['timestamp'] = datetime.utcnow().isoformat()
        normalized['country'] = data.get('country', 'Global')
        
        return normalized
    
    def normalize_user_data(self, data: Dict) -> Dict:
        """
        Normalize user/health profile data.
        
        Args:
            data: Raw user data from API
            
        Returns:
            Normalized dictionary
        """
        normalized = {}
        
        for source_field, target_field in self.FIELD_MAPPINGS.get('heart_rate', {}).items():
            if source_field in data:
                normalized[target_field] = data[source_field]
        
        # Add standardized fields
        normalized['data_type'] = 'user_profile'
        normalized['timestamp'] = datetime.utcnow().isoformat()
        normalized['email'] = data.get('email', '')
        
        return normalized
    
    def normalize_record(self, raw_data: Dict, source: str) -> Optional[Dict]:
        """
        Normalize a single data record based on source API.
        
        Args:
            raw_data: Original data from API
            source: Source API identifier
            
        Returns:
            Normalized dictionary or None if normalization fails
        """
        try:
            if source == 'covid19' or source == 'open_disease':
                return self.normalize_covid_data(raw_data)
            elif source == 'heart_rate':
                return self.normalize_user_data(raw_data)
            else:
                logger.warning(f"Unknown source: {source}")
                return {
                    'raw_data': raw_data,
                    'source': source,
                    'timestamp': datetime.utcnow().isoformat(),
                    'normalized': False
                }
        except Exception as e:
            logger.error(f"Error normalizing {source} data: {str(e)}")
            return None
    
    def normalize_batch(self, records: List[Dict], source: str) -> List[Dict]:
        """
        Normalize multiple records from the same source.
        
        Args:
            records: List of raw data dictionaries
            source: Source API identifier
            
        Returns:
            List of normalized dictionaries (failed items excluded)
        """
        normalized = []
        
        for record in records:
            try:
                normalized_record = self.normalize_record(record, source)
                if normalized_record:
                    normalized.append(normalized_record)
            except Exception as e:
                logger.error(f"Failed to normalize record from {source}: {str(e)}")
                continue
        
        return normalized
    
    def standardize_types(self, data: Dict) -> Dict:
        """
        Ensure consistent data types across all fields.
        
        Args:
            data: Dictionary to standardize
            
        Returns:
            Dictionary with standardized types
        """
        standardized = {}
        
        for key, value in data.items():
            if value is None:
                standardized[key] = None
            elif isinstance(value, bool):
                standardized[key] = value
            elif isinstance(value, (int, float)):
                standardized[key] = float(value) if isinstance(value, float) else int(value)
            elif isinstance(value, str):
                standardized[key] = str(value).strip()
            elif isinstance(value, dict):
                standardized[key] = self.standardize_types(value)
            elif isinstance(value, list):
                standardized[key] = [self.standardize_types(item) if isinstance(item, dict) else item for item in value]
            else:
                standardized[key] = value
        
        return standardized
