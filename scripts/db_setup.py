import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Book, User, ReadingProgress, Bookmark, Review

def init_db():
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Add any initial data if needed
        print("Database tables created successfully!")

def reset_db():
    app = create_app()
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Recreate all tables
        db.create_all()
        print("Database reset successfully!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        reset_db()
    else:
        init_db() 