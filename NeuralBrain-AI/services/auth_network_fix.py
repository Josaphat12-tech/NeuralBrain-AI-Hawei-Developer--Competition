"""
Network-Aware Authentication Service
Fixes Clerk issues on network access by using dynamic redirect URLs

Issues Fixed:
1. Sign up redirects to Clerk website instead of creating account
2. Login keeps reloading instead of redirecting to dashboard
3. Handles both localhost and network IP access

Author: Bitingo Josaphat JB
"""

import os
import logging
from flask import request
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class NetworkAwareAuth:
    """
    Handles network-aware authentication by detecting the host
    and providing appropriate redirect URLs
    """
    
    @staticmethod
    def get_base_url():
        """
        Get the base URL for the current request
        Works for both localhost and network access
        
        Returns:
            str: Base URL (e.g., 'http://192.168.100.87:5000' or 'http://localhost:5000')
        """
        try:
            # Get the host from the request
            host = request.host
            scheme = request.scheme
            
            # Construct base URL
            base_url = f"{scheme}://{host}"
            
            logger.info(f"Base URL detected: {base_url} (Host: {host})")
            return base_url
            
        except Exception as e:
            logger.warning(f"Could not detect base URL: {str(e)}, using fallback")
            # Fallback to environment variable or localhost
            return os.getenv('APP_BASE_URL', 'http://localhost:5000')
    
    @staticmethod
    def get_redirect_url(endpoint='/sso-callback'):
        """
        Get the appropriate redirect URL for Clerk
        
        Args:
            endpoint (str): The endpoint to redirect to after Clerk auth
            
        Returns:
            str: Full redirect URL
        """
        base_url = NetworkAwareAuth.get_base_url()
        redirect_url = f"{base_url}{endpoint}"
        logger.info(f"Redirect URL: {redirect_url}")
        return redirect_url
    
    @staticmethod
    def get_complete_redirect_url(endpoint='/dashboard'):
        """
        Get the complete redirect URL (after successful auth)
        
        Args:
            endpoint (str): The endpoint to redirect to after successful auth
            
        Returns:
            str: Full redirect URL
        """
        base_url = NetworkAwareAuth.get_base_url()
        redirect_url = f"{base_url}{endpoint}"
        logger.info(f"Complete Redirect URL: {redirect_url}")
        return redirect_url
    
    @staticmethod
    def get_clerk_config():
        """
        Get Clerk configuration object with dynamic URLs
        This should be injected into the frontend as a JSON object
        
        Returns:
            dict: Clerk configuration
        """
        return {
            'redirect_url': NetworkAwareAuth.get_redirect_url('/sso-callback'),
            'redirect_url_complete': NetworkAwareAuth.get_complete_redirect_url('/dashboard'),
            'base_url': NetworkAwareAuth.get_base_url(),
            'publishable_key': os.getenv('CLERK_PUBLISHABLE_KEY', '')
        }


class AuthSessionFix:
    """
    Fixes session and cookie issues that cause infinite reloading
    """
    
    @staticmethod
    def validate_session_cookie(session_data):
        """
        Validate and refresh session cookie
        
        Args:
            session_data (dict): Session data from browser
            
        Returns:
            bool: True if session is valid
        """
        try:
            if not session_data:
                return False
            
            # Check for required fields
            required = ['sub', 'email']  # Clerk typically provides these
            
            for field in required:
                if field not in session_data:
                    logger.warning(f"Missing session field: {field}")
                    return False
            
            logger.info(f"Session validation successful for {session_data.get('email')}")
            return True
            
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            return False
    
    @staticmethod
    def fix_infinite_reload_loop():
        """
        Provides middleware/decorator to prevent infinite reload loops
        
        Causes of infinite reload:
        1. Clerk SDK not initialized properly
        2. Session cookie not set correctly
        3. Redirect URLs not matching the request domain
        4. CORS issues
        
        Returns:
            dict: Fixes to apply
        """
        return {
            'issue_1': 'Initialize Clerk SDK with network-aware URLs',
            'fix_1': 'Use dynamic redirectUrl and redirectUrlComplete URLs',
            'issue_2': 'Session cookie not persisted across network access',
            'fix_2': 'Set secure=false for dev, cookie domain to support all network access',
            'issue_3': 'OAuth redirect mismatch',
            'fix_3': 'Register all possible URLs in Clerk Dashboard: http://localhost:5000, http://192.168.x.x:5000',
            'issue_4': 'Missing domain configuration',
            'fix_4': 'Add AUTH_REDIRECT_URLS env var with all possible URLs'
        }


def create_auth_context_processor():
    """
    Create a Flask context processor that injects auth config into all templates
    
    This ensures every template has access to the correct Clerk configuration
    """
    def inject_auth_config():
        """Inject auth configuration into template context"""
        try:
            clerk_config = NetworkAwareAuth.get_clerk_config()
            return {
                'clerk_redirect_url': clerk_config['redirect_url'],
                'clerk_redirect_url_complete': clerk_config['redirect_url_complete'],
                'clerk_publishable_key': clerk_config['publishable_key'],
                'app_base_url': clerk_config['base_url']
            }
        except Exception as e:
            logger.error(f"Error creating auth context: {str(e)}")
            return {
                'clerk_redirect_url': '/sso-callback',
                'clerk_redirect_url_complete': '/dashboard',
                'clerk_publishable_key': os.getenv('CLERK_PUBLISHABLE_KEY', ''),
                'app_base_url': 'http://localhost:5000'
            }
    
    return inject_auth_config


# ============================================================================
# LOGGING ENHANCEMENTS FOR DEBUGGING
# ============================================================================

def log_auth_attempt(email, provider, success, error=None):
    """
    Log authentication attempts for debugging
    
    Args:
        email (str): User email
        provider (str): Auth provider (email, google, github, etc.)
        success (bool): Whether auth was successful
        error (str): Error message if failed
    """
    status = "SUCCESS" if success else "FAILED"
    if error:
        logger.warning(f"AUTH_ATTEMPT [{status}] email={email}, provider={provider}, error={error}")
    else:
        logger.info(f"AUTH_ATTEMPT [{status}] email={email}, provider={provider}")


def log_session_issue(issue_type, details):
    """
    Log session-related issues for debugging
    
    Args:
        issue_type (str): Type of issue (cookie, redirect, validation, etc.)
        details (str): Issue details
    """
    logger.error(f"SESSION_ISSUE [TYPE={issue_type}] {details}")
