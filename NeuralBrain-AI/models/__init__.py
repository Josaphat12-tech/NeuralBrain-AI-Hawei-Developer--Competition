"""
NeuralBrain-AI Models Package
Database models and SQLAlchemy initialization
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .database import HealthDataRecord, IngestionLog, User, UserSettings
