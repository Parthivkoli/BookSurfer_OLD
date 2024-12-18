import os
from datetime import timedelta

class Config:
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://username:password@localhost:5432/reader_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Add PostgreSQL-specific configuration
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 1800,
    }
    
    # Other configurations... 