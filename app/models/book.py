from datetime import datetime
from app import db

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    description = db.Column(db.Text)
    isbn = db.Column(db.String(20))
    publication_year = db.Column(db.Integer)
    genre = db.Column(db.String(50))
    cover_url = db.Column(db.String(500))
    file_path = db.Column(db.String(200))
    file_type = db.Column(db.String(20))
    total_pages = db.Column(db.Integer)
    language = db.Column(db.String(20))
    source = db.Column(db.String(50))
    source_id = db.Column(db.String(100))
    source_url = db.Column(db.String(500))
    accessible_without_login = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    @property
    def can_read(self):
        """Check if the book content is available for reading"""
        return bool(self.file_path or self.content or self.source_url)

    def get_content(self):
        """Get book content, fetching from source if necessary"""
        if not self.content:
            from app.utils.content_fetcher import BookContentFetcher
            book_data = {
                'source': self.source,
                'source_id': self.source_id,
                'download_url': self.source_url
            }
            self.content = BookContentFetcher.fetch_content(book_data)
            if self.content:
                db.session.commit()
        return self.content

    def __repr__(self):
        return f'<Book {self.title}>'

    @property
    def average_rating(self):
        if not self.reviews:
            return 0
        return sum(review.rating for review in self.reviews) / len(self.reviews)
