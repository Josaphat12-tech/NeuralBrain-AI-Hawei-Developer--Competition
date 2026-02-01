
import jwt
import requests
import os
from jwt.algorithms import RSAAlgorithm
import json
from functools import wraps
from flask import request, redirect, url_for, session, current_app


import logging
from datetime import datetime
from models import db, User

logger = logging.getLogger(__name__)

class ClerkAuth:
    def __init__(self):
        self.jwks_cache = None
    
    def get_jwks(self):
        """Fetch JWKS from Clerk"""
        if self.jwks_cache:
            return self.jwks_cache
            
        # Normally this URL comes from the Clerk Dashboard -> API Keys -> JWKS URL
        # But commonly it is https://<your-clerk-domain>/.well-known/jwks.json
        # Check if we can construct it or if we need another env var.
        # For simplicity in this step, we'll try to get it from the standard backend API endpoint if possible,
        # OR we rely on the Frontend to pass a token that we verify.
        
        # ACTUALLY: The best way to verify properly is using the JWKS URL. 
        # Since we don't have the Frontend API URL (clerk.accounts.dev...) in the env yet (only PK),
        # we need to extract it or ask for it.
        # BUT, we can decode the unverified header of the JWT to find the 'iss' (issuer) field.
        pass

    
    def verify_token(self, token):
        """Verify the session token using Clerk's JWKS"""
        try:
            # 1. Decode header to find 'kid' (Key ID)
            unverified_header = jwt.get_unverified_header(token)
            
            # 2. Get JWKS (Public Keys) from the Issuer URL found in the token
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            issuer = unverified_payload.get('iss')
            
            if not issuer:
                logger.error("Token verification failed: No issuer found in token")
                return None
                
            jwks_url = f"{issuer}/.well-known/jwks.json"
            
            # Use cached JWKS if available
            jwks = self.jwks_cache
            
            # If not cached or force refresh needed (e.g. key rotation - simplified here)
            if not jwks:
                logger.info(f"Fetching JWKS from {jwks_url}")
                resp = requests.get(jwks_url)
                if resp.status_code != 200:
                    logger.error(f"Failed to fetch JWKS: {resp.status_code} {resp.text}")
                    return None
                jwks = resp.json()
                self.jwks_cache = jwks
            
            public_key = None
            
            for key in jwks['keys']:
                if key['kid'] == unverified_header['kid']:
                    public_key = RSAAlgorithm.from_jwk(json.dumps(key))
                    break
            
            if not public_key:
                logger.error(f"Public key not found for kid: {unverified_header.get('kid')}")
                # Clear cache in case of key rotation
                self.jwks_cache = None
                return None
                
            # 3. Verify the token signature
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=os.environ.get('CLERK_AUDIENCE'),
                options={"verify_aud": False}
            )
            
            return payload
            
        except requests.exceptions.RequestException as re:
            logger.error(f"Network error fetching JWKS: {str(re)}")
            return None
        except jwt.PyJWTError as je:
            logger.error(f"JWT Verification Error: {str(je)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected Token verification failed: {str(e)}")
            return None

clerk_auth = ClerkAuth()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check Flask Session first (if we saved it there)
        if 'user' in session:
            return f(*args, **kwargs)
            
        # Check for Authorization Header (Bearer Token)
        auth_header = request.headers.get('Authorization')
        token = None
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        # Check for Cookie (Clerk often sets '__session')
        if not token:
            token = request.cookies.get('__session')
            
        if not token:
            return redirect(url_for('views.login'))
            
            
        # Verify Token
        if token:
            # Debug log to see what we are receiving
            masked = token[:10] + '...' if len(token) > 10 else token
            logger.info(f"Verifying token: {masked} (len={len(token)})")
            
        user_payload = clerk_auth.verify_token(token)
        if user_payload:
            # Sync user to local database
            try:
                user_id = user_payload.get('sub')
                # Try multiple common Clerk email claim keys
                email = (
                    user_payload.get('email') or 
                    user_payload.get('email_address') or 
                    user_payload.get('primary_email_address') or
                    ""
                )
                
                # Also try to get names if they exist in the token
                first_name = user_payload.get('given_name') or user_payload.get('first_name')
                last_name = user_payload.get('family_name') or user_payload.get('last_name')
                
                logger.info(f"Syncing user {user_id}. Email: {email}, Name: {first_name} {last_name}")
                logger.info(f"Payload keys: {list(user_payload.keys())}")
                # logger.info(f"Full payload (redacted): { {k: (v if k not in ['email', 'email_address'] else '***') for k, v in user_payload.items()} }")
                
                # Check database
                user = User.query.get(user_id)
                
                if not user:
                    # Create new user
                    user = User(
                        id=user_id,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        role='user'
                    )
                    db.session.add(user)
                    logger.info(f"Created new user record: {user_id}")
                else:
                    # Update existing user if fields are missing but present in token
                    if email and not user.email:
                        user.email = email
                    if first_name and not user.first_name:
                        user.first_name = first_name
                    if last_name and not user.last_name:
                        user.last_name = last_name
                    logger.info(f"Updated existing user record: {user_id}")
                
                # Update last login
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # Add role to payload for session
                user_payload['role'] = user.role
                
            except Exception as e:
                logger.error(f"User sync error: {str(e)}")
                # Continue even if sync fails, don't block login
            
            # Save minimal info to Flask session to avoid re-verifying every single request
            # (In high security, verify every time, but for performance, caching is okay)
            session['user'] = user_payload
            return f(*args, **kwargs)
        else:
            return redirect(url_for('views.login'))
            
    return decorated_function
