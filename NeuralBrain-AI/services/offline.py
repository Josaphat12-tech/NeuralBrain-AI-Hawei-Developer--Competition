"""
Offline-First Support - Caching, Sync Queue, Connection Status
Developed by: Bitingo Josaphat JB
"""

import logging
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages local data caching for offline support"""
    
    def __init__(self, cache_dir: str = 'data/cache'):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = 3600  # Default TTL in seconds
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Cache a value.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_file = self.cache_dir / f"{key}.json"
            
            cache_data = {
                'value': value,
                'timestamp': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(seconds=ttl or self.ttl)).isoformat()
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, default=str)
            
            logger.debug(f"Cached: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache write failed for {key}: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve cached value.
        
        Args:
            key: Cache key
            default: Default value if not found or expired
            
        Returns:
            Cached value or default
        """
        try:
            cache_file = self.cache_dir / f"{key}.json"
            
            if not cache_file.exists():
                return default
            
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check if expired
            expires_at = datetime.fromisoformat(cache_data['expires_at'])
            if datetime.utcnow() > expires_at:
                cache_file.unlink()  # Delete expired cache
                return default
            
            logger.debug(f"Cache hit: {key}")
            return cache_data['value']
        except Exception as e:
            logger.error(f"Cache read failed for {key}: {str(e)}")
            return default
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        return self.get(key) is not None
    
    def delete(self, key: str) -> bool:
        """Delete cached value"""
        try:
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()
                logger.debug(f"Deleted cache: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Cache delete failed for {key}: {str(e)}")
            return False
    
    def clear(self) -> int:
        """Clear all cache files"""
        count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                count += 1
            logger.info(f"Cleared {count} cache files")
            return count
        except Exception as e:
            logger.error(f"Cache clear failed: {str(e)}")
            return count
    
    def get_size(self) -> int:
        """Get total cache size in bytes"""
        total = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                total += cache_file.stat().st_size
            return total
        except Exception as e:
            logger.error(f"Cache size calculation failed: {str(e)}")
            return 0


class SyncQueue:
    """Manages pending operations to sync when connection returns"""
    
    def __init__(self, queue_dir: str = 'data/sync_queue'):
        """
        Initialize sync queue.
        
        Args:
            queue_dir: Directory for queue files
        """
        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.queue: List[Dict] = []
    
    def enqueue(self, operation: str, endpoint: str, method: str, 
                data: Dict = None, priority: int = 0) -> bool:
        """
        Add operation to sync queue.
        
        Args:
            operation: Operation identifier
            endpoint: API endpoint
            method: HTTP method (GET, POST, PUT, DELETE)
            data: Request data
            priority: Priority level (higher = earlier)
            
        Returns:
            True if successful
        """
        try:
            queue_item = {
                'id': self._generate_queue_id(),
                'operation': operation,
                'endpoint': endpoint,
                'method': method,
                'data': data,
                'priority': priority,
                'timestamp': datetime.utcnow().isoformat(),
                'retry_count': 0,
                'max_retries': 3,
                'status': 'pending'
            }
            
            queue_file = self.queue_dir / f"{queue_item['id']}.json"
            with open(queue_file, 'w') as f:
                json.dump(queue_item, f, default=str)
            
            self.queue.append(queue_item)
            logger.info(f"Queued operation: {operation}")
            return True
        except Exception as e:
            logger.error(f"Queue enqueue failed: {str(e)}")
            return False
    
    def get_queue(self) -> List[Dict]:
        """
        Get all pending operations sorted by priority.
        
        Returns:
            List of queued operations
        """
        try:
            self.queue = []
            for queue_file in sorted(self.queue_dir.glob("*.json")):
                with open(queue_file, 'r') as f:
                    queue_item = json.load(f)
                    if queue_item['status'] == 'pending':
                        self.queue.append(queue_item)
            
            # Sort by priority (descending) and timestamp (ascending)
            self.queue.sort(key=lambda x: (-x['priority'], x['timestamp']))
            return self.queue
        except Exception as e:
            logger.error(f"Queue retrieval failed: {str(e)}")
            return []
    
    def mark_processed(self, queue_id: str) -> bool:
        """Mark item as processed"""
        try:
            queue_file = self.queue_dir / f"{queue_id}.json"
            if queue_file.exists():
                with open(queue_file, 'r') as f:
                    queue_item = json.load(f)
                queue_item['status'] = 'processed'
                with open(queue_file, 'w') as f:
                    json.dump(queue_item, f, default=str)
                logger.info(f"Marked as processed: {queue_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Mark processed failed: {str(e)}")
            return False
    
    def clear(self) -> int:
        """Clear all queue files"""
        count = 0
        try:
            for queue_file in self.queue_dir.glob("*.json"):
                queue_file.unlink()
                count += 1
            logger.info(f"Cleared {count} queue items")
            return count
        except Exception as e:
            logger.error(f"Queue clear failed: {str(e)}")
            return count
    
    @staticmethod
    def _generate_queue_id() -> str:
        """Generate unique queue item ID"""
        import uuid
        return f"queue_{uuid.uuid4().hex[:12]}"


class ConnectionStatus:
    """Tracks system connectivity status"""
    
    def __init__(self):
        """Initialize connection tracker"""
        self.is_online = True
        self.last_check = datetime.utcnow()
        self.offline_since = None
    
    def check_connection(self, test_url: str = "https://dns.google.com") -> bool:
        """
        Check internet connectivity.
        
        Args:
            test_url: URL to test connectivity
            
        Returns:
            True if online, False otherwise
        """
        try:
            import requests
            response = requests.head(test_url, timeout=3)
            is_online = response.status_code < 500
        except Exception as e:
            is_online = False
            logger.debug(f"Connection check failed: {str(e)}")
        
        # Update status
        prev_status = self.is_online
        self.is_online = is_online
        self.last_check = datetime.utcnow()
        
        if not is_online and prev_status:
            # Just went offline
            self.offline_since = datetime.utcnow()
            logger.warning("🔴 System went offline")
        elif is_online and not prev_status:
            # Just came online
            offline_duration = (datetime.utcnow() - self.offline_since).total_seconds()
            logger.info(f"🟢 System back online (was offline for {offline_duration:.0f}s)")
            self.offline_since = None
        
        return is_online
    
    def get_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        return {
            'online': self.is_online,
            'last_check': self.last_check.isoformat(),
            'offline_since': self.offline_since.isoformat() if self.offline_since else None,
            'offline_duration_seconds': (
                (datetime.utcnow() - self.offline_since).total_seconds()
                if self.offline_since else 0
            )
        }


# Global instances
_cache_manager: Optional[CacheManager] = None
_sync_queue: Optional[SyncQueue] = None
_connection_status: Optional[ConnectionStatus] = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def get_sync_queue() -> SyncQueue:
    """Get or create global sync queue"""
    global _sync_queue
    if _sync_queue is None:
        _sync_queue = SyncQueue()
    return _sync_queue


def get_connection_status() -> ConnectionStatus:
    """Get or create global connection status tracker"""
    global _connection_status
    if _connection_status is None:
        _connection_status = ConnectionStatus()
    return _connection_status
