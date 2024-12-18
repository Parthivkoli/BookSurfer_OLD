from app.extensions import db
from datetime import datetime

class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255))
    content = db.Column(db.Text)  # Full book content
    summary = db.Column(db.Text)  # Book summary
    cover_url = db.Column(db.String(500))
    source_url = db.Column(db.String(500))
    source = db.Column(db.String(50))  # e.g., 'gutenberg', 'openlibrary'
    source_id = db.Column(db.String(100))  # ID from the source platform
    file_path = db.Column(db.String(500))  # For locally stored files
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    category = db.Column(db.String(50), default='Public')
    accessible_without_login = db.Column(db.Boolean, default=True)
    
    # Relationships
    bookmarks = db.relationship('Bookmark', backref='book', lazy=True)
    reading_progress = db.relationship('ReadingProgress', backref='book', lazy=True)
    reviews = db.relationship('Review', backref='book', lazy=True)
    
    def __repr__(self):
        return f'<Book {self.title} by {self.author}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'cover_url': self.cover_url,
            'source': self.source,
            'source_id': self.source_id,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'summary': self.summary
        } 