"""
Health Data Ingestion Service
Fetches data from free public health APIs with error handling and retry logic
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from config import (
    HEALTH_APIS,
    API_TIMEOUT,
    API_RETRY_ATTEMPTS,
    API_RETRY_DELAY,
    RAW_DATA_FILE,
)

logger = logging.getLogger(__name__)


class DataIngestionService:
    """
    Handles fetching health data from public APIs.
    
    Implements:
    - Retry logic with exponential backoff
    - Timeout handling
    - Graceful failure management
    - Data persistence to JSON
    """
    
    def __init__(self):
        """Initialize the ingestion service."""
        self.timeout = API_TIMEOUT
        self.retry_attempts = API_RETRY_ATTEMPTS
        self.retry_delay = API_RETRY_DELAY
        self.apis = HEALTH_APIS
    
    def fetch_from_api(self, api_key: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Fetch data from a specific API with retry logic.
        
        Args:
            api_key: Key in HEALTH_APIS config
            
        Returns:
            Tuple of (data_dict, error_message)
            - If successful: (data, None)
            - If failed: (None, error_message)
        """
        if api_key not in self.apis:
            return None, f"Unknown API: {api_key}"
        
        api_config = self.apis[api_key]
        url = api_config['url']
        
        for attempt in range(1, self.retry_attempts + 1):
            try:
                logger.info(f"Fetching {api_key} from {url} (attempt {attempt}/{self.retry_attempts})")
                
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Successfully fetched data from {api_key}")
                return data, None
                
            except requests.exceptions.Timeout:
                error_msg = f"Timeout on {api_key} (attempt {attempt})"
                logger.warning(error_msg)
                
            except requests.exceptions.ConnectionError:
                error_msg = f"Connection error on {api_key} (attempt {attempt})"
                logger.warning(error_msg)
                
            except requests.exceptions.HTTPError as e:
                error_msg = f"HTTP error {e.response.status_code} from {api_key} (attempt {attempt})"
                logger.warning(error_msg)
                
            except json.JSONDecodeError:
                error_msg = f"Invalid JSON response from {api_key} (attempt {attempt})"
                logger.error(error_msg)
                return None, error_msg
                
            except Exception as e:
                error_msg = f"Unexpected error from {api_key} (attempt {attempt}): {str(e)}"
                logger.error(error_msg)
            
            # Delay before retry (except on last attempt)
            if attempt < self.retry_attempts:
                time.sleep(self.retry_delay * attempt)  # Exponential backoff
        
        final_error = f"Failed to fetch {api_key} after {self.retry_attempts} attempts"
        return None, final_error
    
    def ingest_all_sources(self) -> Dict:
        """
        Fetch data from all configured health APIs.
        
        Returns:
            Dictionary with ingestion results:
            {
                'timestamp': ISO string,
                'total_apis': int,
                'successful': int,
                'failed': int,
                'sources': {
                    'api_name': {
                        'status': 'success|failed',
                        'data': dict or None,
                        'error': str or None,
                        'records': int
                    }
                }
            }
        """
        ingestion_result = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_apis': len(self.apis),
            'successful': 0,
            'failed': 0,
            'sources': {}
        }
        
        raw_data_collection = {
            'timestamp': datetime.utcnow().isoformat(),
            'sources': {}
        }
        
        for api_key in self.apis:
            data, error = self.fetch_from_api(api_key)
            
            if error is None and data is not None:
                ingestion_result['sources'][api_key] = {
                    'status': 'success',
                    'data': data,
                    'error': None,
                    'records': len(data) if isinstance(data, list) else 1
                }
                ingestion_result['successful'] += 1
                raw_data_collection['sources'][api_key] = {
                    'data': data,
                    'fetched_at': datetime.utcnow().isoformat()
                }
                logger.info(f"✓ {api_key}: {ingestion_result['sources'][api_key]['records']} records")
            else:
                ingestion_result['sources'][api_key] = {
                    'status': 'failed',
                    'data': None,
                    'error': error,
                    'records': 0
                }
                ingestion_result['failed'] += 1
                logger.error(f"✗ {api_key}: {error}")
        
        # Persist raw data to JSON file
        self._save_raw_data(raw_data_collection)
        
        return ingestion_result
    
    def _save_raw_data(self, data: Dict) -> bool:
        """
        Save raw ingested data to JSON file.
        
        Args:
            data: Data dictionary to persist
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(RAW_DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Raw data saved to {RAW_DATA_FILE}")
            return True
        except Exception as e:
            logger.error(f"Failed to save raw data: {str(e)}")
            return False
    
    @staticmethod
    def load_raw_data() -> Optional[Dict]:
        """
        Load previously ingested raw data from JSON file.
        
        Returns:
            Dictionary of raw data or None if not found
        """
        try:
            with open(RAW_DATA_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Raw data file not found: {RAW_DATA_FILE}")
            return None
        except Exception as e:
            logger.error(f"Error loading raw data: {str(e)}")
            return None
