"""
NeuralBrain-AI Database Models
Defines the structure for health data records and ingestion logs
"""

from datetime import datetime
from .import db
from sqlalchemy.types import JSON


class HealthDataRecord(db.Model):
    """
    Stores normalized health data records.
    
    Attributes:
        id: Unique identifier
        data_source: Origin API (e.g., 'covid19', 'heart_rate')
        raw_data: JSON object containing original data
        processed_data: JSON object containing normalized data
        metrics: JSON object containing extracted health metrics
        timestamp: When the record was ingested
        last_updated: Last modification timestamp
        status: Record status (valid, invalid, pending)
    """
    __tablename__ = 'health_data_records'
    
    id = db.Column(db.Integer, primary_key=True)
    data_source = db.Column(db.String(100), nullable=False, index=True)
    raw_data = db.Column(JSON, nullable=True)
    processed_data = db.Column(JSON, nullable=True)
    metrics = db.Column(JSON, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='pending', index=True)
    validation_notes = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        """Convert record to dictionary."""
        return {
            'id': self.id,
            'data_source': self.data_source,
            'raw_data': self.raw_data,
            'processed_data': self.processed_data,
            'metrics': self.metrics,
            'timestamp': self.timestamp.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'status': self.status,
            'validation_notes': self.validation_notes
        }
    
    def __repr__(self):
        return f'<HealthDataRecord {self.id} from {self.data_source}>'


class User(db.Model):
    """
    Stores user authentication and profile details.
    Synced from Clerk authentication.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.String(100), primary_key=True) # Clerk User ID
    email = db.Column(db.String(150), nullable=False, unique=True, index=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)  # URL to profile image
    role = db.Column(db.String(20), default='user')
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'profile_image': self.profile_image,
            'role': self.role,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    def __repr__(self):
        return f'<User {self.email}>'
class IngestionLog(db.Model):
    """
    Tracks data ingestion operations and their outcomes.
    
    Attributes:
        id: Unique identifier
        api_source: Which API was queried
        status: Ingestion status (success, failed, partial)
        records_fetched: Number of records retrieved
        records_processed: Number of records successfully processed
        error_message: Error details if applicable
        execution_time: How long ingestion took (seconds)
        timestamp: When ingestion occurred
    """
    __tablename__ = 'ingestion_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    api_source = db.Column(db.String(100), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='pending')
    records_fetched = db.Column(db.Integer, default=0)
    records_processed = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    execution_time = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    details = db.Column(JSON, nullable=True)
    
    def to_dict(self):
        """Convert log to dictionary."""
        return {
            'id': self.id,
            'api_source': self.api_source,
            'status': self.status,
            'records_fetched': self.records_fetched,
            'records_processed': self.records_processed,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details
        }
    
    def __repr__(self):
        return f'<IngestionLog {self.id} from {self.api_source} [{self.status}]>'
