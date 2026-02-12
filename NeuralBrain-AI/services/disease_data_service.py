"""
Disease Data Service - PRODUCTION-GRADE (Fixed)

This service provides:
- Global statistics with HTTP validation
- Country-specific data with retry logic
- Historical trends (60-day) with timeout enforcement
- Regional outbreaks with fallback
- Data quality tracking
- Staleness indicators

Data Source: https://disease.sh/v3/covid-19/

CRITICAL FIXES:
✅ HTTP status validation (not silent failures)
✅ Retry with exponential backoff
✅ Timeout enforcement  
✅ Data quality tracking
✅ Staleness timestamps
✅ False-positive log prevention
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import time

logger = logging.getLogger(__name__)

class DiseaseDataService:
    """Fetches real-time disease data from disease.sh API"""
    
    BASE_URL = "https://disease.sh/v3/covid-19"
    TIMEOUT = 10
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds (exponential backoff)
    
    # Track data freshness
    _last_fetch_time = None
    _last_fetch_status = "NOT_ATTEMPTED"
    _last_successful_fetch = None
    
    @staticmethod
    def _make_request_with_retry(endpoint: str, max_retries: int = MAX_RETRIES) -> Optional[Dict]:
        """
        Make HTTP request with exponential backoff retry
        
        Returns:
            Response JSON on success
            None on complete failure (logs error)
        """
        url = f"{DiseaseDataService.BASE_URL}{endpoint}"
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Fetching {endpoint} (attempt {attempt + 1}/{max_retries})")
                
                response = requests.get(
                    url,
                    timeout=DiseaseDataService.TIMEOUT,
                    headers={'User-Agent': 'NeuralBrain-AI/1.0'}
                )
                
                # CRITICAL: Validate HTTP status
                if response.status_code != 200:
                    logger.warning(f"⚠️ HTTP {response.status_code} from {endpoint}")
                    
                    if attempt < max_retries - 1:
                        wait_time = DiseaseDataService.RETRY_DELAY * (2 ** attempt)
                        logger.info(f"⏳ Retry in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"❌ Failed after {max_retries} retries: HTTP {response.status_code}")
                        DiseaseDataService._last_fetch_status = f"FAILED_HTTP_{response.status_code}"
                        return None
                
                # Parse JSON
                data = response.json()
                
                # Track successful fetch
                DiseaseDataService._last_fetch_time = datetime.utcnow()
                DiseaseDataService._last_fetch_status = "SUCCESS"
                DiseaseDataService._last_successful_fetch = data
                
                logger.info(f"✅ Successfully fetched {endpoint}")
                return data
                
            except requests.Timeout:
                logger.warning(f"⏱️ Timeout on {endpoint} (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(DiseaseDataService.RETRY_DELAY * (2 ** attempt))
                    continue
                else:
                    logger.error(f"❌ Timeout after {max_retries} attempts")
                    DiseaseDataService._last_fetch_status = "TIMEOUT"
                    return None
                    
            except requests.ConnectionError as e:
                logger.warning(f"🌐 Connection error on {endpoint}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(DiseaseDataService.RETRY_DELAY * (2 ** attempt))
                    continue
                else:
                    logger.error(f"❌ Connection failed after {max_retries} attempts")
                    DiseaseDataService._last_fetch_status = "CONNECTION_ERROR"
                    return None
                    
            except json.JSONDecodeError:
                logger.error(f"❌ Invalid JSON from {endpoint}")
                DiseaseDataService._last_fetch_status = "INVALID_JSON"
                return None
                
            except Exception as e:
                logger.error(f"❌ Unexpected error on {endpoint}: {str(e)}")
                DiseaseDataService._last_fetch_status = f"ERROR_{type(e).__name__}"
                return None
        
        DiseaseDataService._last_fetch_status = "MAX_RETRIES_EXCEEDED"
        return None
    
    @staticmethod
    def get_global_stats() -> Dict[str, Any]:
        """
        GET /all - Global COVID-19 statistics
        
        Returns:
        {
            "cases": 700000000,
            "deaths": 7000000,
            "recovered": 600000000,
            "todayCases": 500000,
            "todayDeaths": 5000,
            "data_status": "FRESH" | "CACHED" | "FALLBACK",
            "data_age_seconds": 0,
            ...
        }
        """
        try:
            logger.info("📊 Fetching global COVID-19 stats from disease.sh...")
            
            data = DiseaseDataService._make_request_with_retry('/all')
            
            if data is None:
                logger.error("❌ Global stats fetch FAILED - using fallback")
                fallback = DiseaseDataService._get_fallback_global_stats()
                fallback['data_status'] = 'FALLBACK'
                fallback['data_error'] = DiseaseDataService._last_fetch_status
                return fallback
            
            # Add metadata
            data['data_status'] = 'FRESH'
            data['data_timestamp'] = DiseaseDataService._last_fetch_time.isoformat() if DiseaseDataService._last_fetch_time else None
            data['data_age_seconds'] = 0
            
            logger.info(f"✅ Global stats: {data.get('cases', 0):,} total cases")
            return data
            
        except Exception as e:
            logger.error(f"❌ Unexpected error in get_global_stats: {str(e)}")
            fallback = DiseaseDataService._get_fallback_global_stats()
            fallback['data_status'] = 'FALLBACK'
            fallback['data_error'] = str(e)
            return fallback
    
    @staticmethod
    def get_countries_data() -> List[Dict[str, Any]]:
        """
        GET /countries - Per-country statistics with coordinates
        
        Returns list of:
        {
            "country": "USA",
            "countryInfo": {"_id": 840, "iso2": "US", "iso3": "USA", "lat": 37.0902, "long": -95.7129},
            "cases": 103000000,
            "deaths": 1100000,
            "data_status": "FRESH" | "FALLBACK"
        }
        """
        try:
            logger.info("🌍 Fetching per-country COVID-19 data...")
            
            data = DiseaseDataService._make_request_with_retry('/countries')
            
            if data is None:
                logger.error("❌ Countries data fetch FAILED - using fallback")
                fallback = DiseaseDataService._get_fallback_countries_data()
                for item in fallback:
                    item['data_status'] = 'FALLBACK'
                return fallback
            
            # Sort by cases descending
            data_sorted = sorted(data, key=lambda x: x.get('cases', 0), reverse=True)
            
            # Add metadata
            for item in data_sorted:
                item['data_status'] = 'FRESH'
                item['data_timestamp'] = DiseaseDataService._last_fetch_time.isoformat() if DiseaseDataService._last_fetch_time else None
            
            logger.info(f"✅ Retrieved data for {len(data_sorted)} countries")
            return data_sorted
            
        except Exception as e:
            logger.error(f"❌ Unexpected error in get_countries_data: {str(e)}")
            fallback = DiseaseDataService._get_fallback_countries_data()
            for item in fallback:
                item['data_status'] = 'FALLBACK'
                item['data_error'] = str(e)
            return fallback
    
    @staticmethod
    def get_historical_data(days: int = 60) -> List[Dict[str, Any]]:
        """
        GET /historical/all?lastdays={days}
        
        Returns 60-day historical trend data for charting
        
        Format:
        [{
            "date": "12/31/2024",
            "cases": 700000000,
            "deaths": 7000000,
            "data_status": "FRESH" | "FALLBACK"
        }, ...]
        """
        try:
            logger.info(f"📈 Fetching {days}-day historical data...")
            
            data = DiseaseDataService._make_request_with_retry(f'/historical/all?lastdays={days}')
            
            if data is None:
                logger.error(f"❌ Historical data fetch FAILED - using fallback")
                fallback = DiseaseDataService._get_fallback_historical_data(days)
                for item in fallback:
                    item['data_status'] = 'FALLBACK'
                return fallback
            
            # Transform format if needed
            result = []
            if isinstance(data, dict):
                # Data is in format: {'cases': {date: value, ...}, 'deaths': {date: value, ...}, 'recovered': {...}}
                # Need to combine these back to: [{date: x, cases: y, deaths: z}, ...]
                
                cases_data = data.get('cases', {})
                deaths_data = data.get('deaths', {})
                recovered_data = data.get('recovered', {})
                
                # Get all unique dates from cases data (primary source)
                if isinstance(cases_data, dict):
                    for date_str, case_count in cases_data.items():
                        result.append({
                            'date': date_str,
                            'cases': case_count,
                            'deaths': deaths_data.get(date_str, 0),
                            'recovered': recovered_data.get(date_str, 0),
                            'data_status': 'FRESH',
                            'data_timestamp': DiseaseDataService._last_fetch_time.isoformat() if DiseaseDataService._last_fetch_time else None
                        })
            
            logger.info(f"✅ Retrieved {len(result)} days of historical data")
            return result
            
        except Exception as e:
            logger.error(f"❌ Unexpected error in get_historical_data: {str(e)}")
            fallback = DiseaseDataService._get_fallback_historical_data(days)
            for item in fallback:
                item['data_status'] = 'FALLBACK'
                item['data_error'] = str(e)
            return fallback
    
    @staticmethod
    def get_regional_outbreak_risk() -> List[Dict[str, Any]]:
        """Calculate regional outbreak risk from countries data"""
        try:
            countries = DiseaseDataService.get_countries_data()
            
            risks = []
            for country in countries[:20]:  # Top 20 countries
                cases = country.get('cases', 0)
                deaths = country.get('deaths', 0)
                population = country.get('population', 1)
                
                # Risk score calculation
                if population > 0:
                    case_rate = (cases / population) * 100000 if population > 0 else 0
                    death_rate = (deaths / cases * 100) if cases > 0 else 0
                else:
                    case_rate = 0
                    death_rate = 0
                
                risk_score = min(100, (case_rate / 10) + (death_rate * 2))
                
                risks.append({
                    'country': country.get('country', 'Unknown'),
                    'cases': cases,
                    'deaths': deaths,
                    'riskScore': round(risk_score, 1),
                    'data_status': country.get('data_status', 'UNKNOWN')
                })
            
            logger.info(f"✅ Calculated outbreak risk for {len(risks)} regions")
            return risks
            
        except Exception as e:
            logger.error(f"❌ Error calculating regional risk: {str(e)}")
            return DiseaseDataService._get_fallback_regional_risks()
    
    @staticmethod
    def get_data_status() -> Dict[str, Any]:
        """Return current data fetch status"""
        return {
            'last_fetch_status': DiseaseDataService._last_fetch_status,
            'last_fetch_time': DiseaseDataService._last_fetch_time.isoformat() if DiseaseDataService._last_fetch_time else None,
            'is_healthy': DiseaseDataService._last_fetch_status == 'SUCCESS',
            'data_available': DiseaseDataService._last_successful_fetch is not None
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FALLBACK DATA (Only used when API fails)
    # ═══════════════════════════════════════════════════════════════════════════
    
    @staticmethod
    def _get_fallback_global_stats() -> Dict[str, Any]:
        """Fallback global stats (realistic data)"""
        return {
            'cases': 765432100,
            'deaths': 7654321,
            'recovered': 698765432,
            'todayCases': 250000,
            'todayDeaths': 2500,
            'todayRecovered': 200000,
            'active': 59012347,
            'data_status': 'FALLBACK',
            'data_error': 'API_UNAVAILABLE'
        }
    
    @staticmethod
    def _get_fallback_countries_data() -> List[Dict[str, Any]]:
        """Fallback countries data (top 10 countries)"""
        return [
            {'country': 'USA', 'cases': 103000000, 'deaths': 1100000, 'population': 331000000, 'countryInfo': {'lat': 37.0902, 'long': -95.7129}},
            {'country': 'India', 'cases': 45000000, 'deaths': 520000, 'population': 1380000000, 'countryInfo': {'lat': 20.5937, 'long': 78.9629}},
            {'country': 'Brazil', 'cases': 34000000, 'deaths': 680000, 'population': 212000000, 'countryInfo': {'lat': -14.2350, 'long': -51.9253}},
            {'country': 'France', 'cases': 32000000, 'deaths': 160000, 'population': 65000000, 'countryInfo': {'lat': 46.2276, 'long': 2.2137}},
            {'country': 'Germany', 'cases': 33000000, 'deaths': 150000, 'population': 83000000, 'countryInfo': {'lat': 51.1657, 'long': 10.4515}},
            {'country': 'UK', 'cases': 24000000, 'deaths': 200000, 'population': 67000000, 'countryInfo': {'lat': 55.3781, 'long': -3.4360}},
            {'country': 'Italy', 'cases': 22000000, 'deaths': 180000, 'population': 60000000, 'countryInfo': {'lat': 41.8719, 'long': 12.5674}},
            {'country': 'Japan', 'cases': 21000000, 'deaths': 95000, 'population': 125000000, 'countryInfo': {'lat': 36.2048, 'long': 138.2529}},
            {'country': 'Canada', 'cases': 15000000, 'deaths': 45000, 'population': 38000000, 'countryInfo': {'lat': 56.1304, 'long': -106.3468}},
            {'country': 'Spain', 'cases': 14000000, 'deaths': 110000, 'population': 47000000, 'countryInfo': {'lat': 40.4637, 'long': -3.7492}},
        ]
    
    @staticmethod
    def _get_fallback_historical_data(days: int = 60) -> List[Dict[str, Any]]:
        """Fallback historical data (realistic trend)"""
        result = []
        base_date = datetime.utcnow() - timedelta(days=days)
        base_cases = 600000000
        
        for i in range(days):
            current_date = base_date + timedelta(days=i)
            # Simulate realistic trend (slight growth)
            cases = int(base_cases + (i * 2700000))
            deaths = int(cases * 0.01)
            
            result.append({
                'date': current_date.strftime('%m/%d/%Y'),
                'cases': cases,
                'deaths': deaths
            })
        
        return result
    
    @staticmethod
    def _get_fallback_regional_risks() -> List[Dict[str, Any]]:
        """Fallback regional risks"""
        return [
            {'country': 'USA', 'cases': 103000000, 'deaths': 1100000, 'riskScore': 85.5},
            {'country': 'India', 'cases': 45000000, 'deaths': 520000, 'riskScore': 72.3},
            {'country': 'Brazil', 'cases': 34000000, 'deaths': 680000, 'riskScore': 78.9},
            {'country': 'France', 'cases': 32000000, 'deaths': 160000, 'riskScore': 65.2},
            {'country': 'Germany', 'cases': 33000000, 'deaths': 150000, 'riskScore': 62.8},
        ]
