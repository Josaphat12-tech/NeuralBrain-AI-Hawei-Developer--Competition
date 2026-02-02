"""
NeuralBrain-AI Configuration Module
Centralized configuration for Flask application
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Ensure data directory exists
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Flask Configuration
DEBUG = os.getenv('FLASK_DEBUG', False)
TESTING = os.getenv('FLASK_TESTING', False)
SECRET_KEY = os.getenv('SECRET_KEY', 'neuralbrain-dev-key-change-in-production')

# Fix for SQLAlchemy 1.4+ and use Psycopg 3 driver
uri = os.getenv('DATABASE_URL')
if uri:
    if uri.startswith('postgres://'):
        uri = uri.replace('postgres://', 'postgresql+psycopg://', 1)
    elif uri.startswith('postgresql://'):
        uri = uri.replace('postgresql://', 'postgresql+psycopg://', 1)

_db_path = os.path.join(DATA_DIR, "neuralbrain.db")
# SQLite URI - use 4 slashes for absolute path on Unix
SQLALCHEMY_DATABASE_URI = uri or f'sqlite:////{os.path.abspath(_db_path)}'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Application Metadata
APP_NAME = "NeuralBrain-AI"
APP_VERSION = "1.0.0"
AUTHOR = "Bitingo Josaphat JB"
COPYRIGHT_YEAR = 2026

# API Configuration
API_TIMEOUT = 15  # seconds
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY = 2  # seconds

# Data Management (already created DATA_DIR above)
RAW_DATA_FILE = os.path.join(DATA_DIR, 'raw_data.json')
PROCESSED_DATA_FILE = os.path.join(DATA_DIR, 'processed_data.json')

# Health Data APIs (Free & Public)
HEALTH_APIS = {
    'open_disease': {
        'name': 'Open Disease',
        'url': 'https://disease.sh/v3/covid-19',
        'description': 'COVID-19 epidemiological data',
        'free': True
    },
    'heart_rate': {
        'name': 'Fake API',
        'url': 'https://fakerapi.it/api/v1/users',
        'description': 'Sample health metrics',
        'free': True
    }
}

# Validation Rules
VALIDATION_RULES = {
    'temperature': {'min': 35.0, 'max': 42.0, 'unit': 'Celsius'},
    'heart_rate': {'min': 30, 'max': 200, 'unit': 'bpm'},
    'blood_pressure_sys': {'min': 60, 'max': 200, 'unit': 'mmHg'},
    'blood_pressure_dia': {'min': 40, 'max': 120, 'unit': 'mmHg'},
    'oxygen_saturation': {'min': 70, 'max': 100, 'unit': '%'},
}

# Session Configuration
PERMANENT_SESSION_LIFETIME = timedelta(days=7)
SESSION_REFRESH_EACH_REQUEST = True
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
