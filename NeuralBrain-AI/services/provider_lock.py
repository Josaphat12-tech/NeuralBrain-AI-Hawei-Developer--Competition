"""
Provider Lock System - Deterministic AI Provider Routing

Implements atomic provider locking to ensure only ONE provider handles all AI tasks
at any given time, with clean failover on explicit failure conditions.

Key Principles:
- ✅ Single provider per runtime session
- ✅ Atomic lock acquire/release
- ✅ Persistent lock state
- ✅ Complete audit trail
- ✅ Manual override capability
"""

import logging
import json
import os
from datetime import datetime
from threading import RLock
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Provider health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ProviderLockManager:
    """
    Manages provider locking with atomic operations and audit trail.
    
    Ensures deterministic single-provider execution with clean failover.
    """
    
    # Lock state file location
    LOCK_STATE_FILE = os.path.join(os.path.dirname(__file__), '..', 'cache', 'provider_lock.json')
    
    # Providers in priority order (first = default)
    PROVIDER_PRIORITY = [
        'openai',
        'gemini',
        'groq',
        'cloudflare',
        'huggingface'
    ]
    
    def __init__(self):
        """Initialize provider lock manager"""
        self._lock = RLock()  # Thread-safe operations
        self._locked_provider = None
        self._lock_acquired_at = None
        self._failure_count = 0
        self._consecutive_failures = 0
        self._status_history = []
        self._audit_trail = []
        
        logger.info("🔒 ProviderLockManager initialized")
        
        # Create cache directory if needed
        os.makedirs(os.path.dirname(self.LOCK_STATE_FILE), exist_ok=True)
        
        # Load persisted state
        self._load_state()
    
    def acquire_lock(self, provider_name: str) -> bool:
        """
        Acquire lock for a provider (atomic operation)
        
        Args:
            provider_name: Provider to lock (must be in PROVIDER_PRIORITY)
            
        Returns:
            bool: True if lock acquired successfully
        """
        with self._lock:
            if provider_name not in self.PROVIDER_PRIORITY:
                logger.error(f"❌ Unknown provider: {provider_name}")
                return False
            
            # Release previous lock if exists
            if self._locked_provider and self._locked_provider != provider_name:
                self._audit_log("lock_release", self._locked_provider, {"reason": "switching_provider"})
            
            self._locked_provider = provider_name
            self._lock_acquired_at = datetime.utcnow()
            self._consecutive_failures = 0
            
            # Log acquisition
            log_msg = f"✅ Provider lock acquired: {provider_name}"
            logger.info(log_msg)
            self._audit_log("lock_acquire", provider_name, {
                "acquired_at": self._lock_acquired_at.isoformat()
            })
            
            # Persist state
            self._save_state()
            
            return True
    
    def release_lock(self, reason: str = "manual_release") -> bool:
        """
        Release lock on current provider (atomic operation)
        
        Args:
            reason: Reason for release (quota_exhaustion, auth_failure, etc)
            
        Returns:
            bool: True if lock released
        """
        with self._lock:
            if not self._locked_provider:
                logger.warning("⚠️ No lock to release")
                return False
            
            previous_provider = self._locked_provider
            self._locked_provider = None
            
            logger.warning(f"⚠️ Provider lock released: {previous_provider} ({reason})")
            self._audit_log("lock_release", previous_provider, {"reason": reason})
            
            self._save_state()
            return True
    
    def get_locked_provider(self) -> Optional[str]:
        """Get currently locked provider"""
        with self._lock:
            return self._locked_provider
    
    def is_locked(self, provider_name: str) -> bool:
        """Check if specific provider is locked"""
        with self._lock:
            return self._locked_provider == provider_name
    
    def increment_failure_count(self, increment: int = 1) -> int:
        """
        Increment failure count for locked provider
        
        Args:
            increment: Amount to increment
            
        Returns:
            int: New failure count
        """
        with self._lock:
            self._failure_count += increment
            self._consecutive_failures += increment
            
            logger.warning(
                f"⚠️ Provider failure recorded: {self._locked_provider} "
                f"(consecutive: {self._consecutive_failures}, total: {self._failure_count})"
            )
            
            self._audit_log("failure_recorded", self._locked_provider, {
                "consecutive": self._consecutive_failures,
                "total": self._failure_count
            })
            
            self._save_state()
            return self._consecutive_failures
    
    def reset_failure_count(self) -> None:
        """Reset failure counts on successful operation"""
        with self._lock:
            if self._failure_count > 0 or self._consecutive_failures > 0:
                logger.info(f"✅ Provider health recovered: {self._locked_provider}")
                self._audit_log("health_recovered", self._locked_provider, {
                    "previous_consecutive": self._consecutive_failures,
                    "previous_total": self._failure_count
                })
            
            self._consecutive_failures = 0
            self._save_state()
    
    def get_next_provider(self) -> Optional[str]:
        """
        Get next provider in priority order
        
        Returns:
            str: Next provider to try, or None if end of list
        """
        with self._lock:
            current = self._locked_provider
            if not current:
                return self.PROVIDER_PRIORITY[0]  # Return first in priority
            
            try:
                current_idx = self.PROVIDER_PRIORITY.index(current)
                if current_idx + 1 < len(self.PROVIDER_PRIORITY):
                    return self.PROVIDER_PRIORITY[current_idx + 1]
            except ValueError:
                pass
            
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive lock status
        
        Returns:
            dict: Status information
        """
        with self._lock:
            return {
                "locked_provider": self._locked_provider,
                "lock_acquired_at": self._lock_acquired_at.isoformat() if self._lock_acquired_at else None,
                "consecutive_failures": self._consecutive_failures,
                "total_failures": self._failure_count,
                "is_locked": self._locked_provider is not None,
                "next_provider": self.get_next_provider(),
                "provider_priority": self.PROVIDER_PRIORITY,
                "audit_trail_count": len(self._audit_trail)
            }
    
    def get_audit_trail(self, limit: int = 50) -> list:
        """
        Get recent audit trail entries
        
        Args:
            limit: Max entries to return
            
        Returns:
            list: Recent audit trail entries
        """
        with self._lock:
            return self._audit_trail[-limit:]
    
    def _audit_log(self, event_type: str, provider_name: str, details: Dict[str, Any] = None) -> None:
        """
        Log event to audit trail
        
        Args:
            event_type: Type of event
            provider_name: Provider involved
            details: Additional details
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "provider": provider_name,
            "details": details or {}
        }
        
        self._audit_trail.append(entry)
        
        # Keep only last 1000 entries
        if len(self._audit_trail) > 1000:
            self._audit_trail = self._audit_trail[-1000:]
    
    def _save_state(self) -> None:
        """Persist lock state to disk"""
        try:
            state = {
                "locked_provider": self._locked_provider,
                "lock_acquired_at": self._lock_acquired_at.isoformat() if self._lock_acquired_at else None,
                "failure_count": self._failure_count,
                "consecutive_failures": self._consecutive_failures,
                "saved_at": datetime.utcnow().isoformat()
            }
            
            with open(self.LOCK_STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to save lock state: {str(e)}")
    
    def _load_state(self) -> None:
        """Load lock state from disk if exists"""
        try:
            if os.path.exists(self.LOCK_STATE_FILE):
                with open(self.LOCK_STATE_FILE, 'r') as f:
                    state = json.load(f)
                
                self._locked_provider = state.get("locked_provider")
                self._failure_count = state.get("failure_count", 0)
                self._consecutive_failures = state.get("consecutive_failures", 0)
                
                if state.get("lock_acquired_at"):
                    self._lock_acquired_at = datetime.fromisoformat(state["lock_acquired_at"])
                
                logger.info(f"✅ Lock state loaded: {self._locked_provider}")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to load lock state: {str(e)}")
            # Start fresh if load fails
            self._locked_provider = self.PROVIDER_PRIORITY[0]
            self._lock_acquired_at = datetime.utcnow()
            self._save_state()


# Global singleton instance
_lock_manager_instance = None


def get_provider_lock_manager() -> ProviderLockManager:
    """Get or create singleton instance"""
    global _lock_manager_instance
    if _lock_manager_instance is None:
        _lock_manager_instance = ProviderLockManager()
    return _lock_manager_instance
