from datetime import datetime
from app import db

class ReadingProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    current_page = db.Column(db.Integer, default=1)
    last_read = db.Column(db.DateTime, default=datetime.utcnow)
    completion_percentage = db.Column(db.Float, default=0)
    reading_time = db.Column(db.Integer, default=0)  # in seconds
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)

    def __repr__(self):
        return f'<ReadingProgress {self.user_id}:{self.book_id}>'

    def update_progress(self, current_page, total_pages):
        self.current_page = current_page
        self.completion_percentage = (current_page / total_pages) * 100
        self.last_read = datetime.utcnow()
