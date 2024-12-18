from datetime import datetime
from app import db

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_number = db.Column(db.Integer, nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)

    def __repr__(self):
        return f'<Bookmark {self.user_id}:{self.book_id}:{self.page_number}>'
