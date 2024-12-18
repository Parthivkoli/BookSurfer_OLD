import json
import logging
from datetime import datetime, timedelta
from app.extensions import db
from app.models import Book
import os
from flask import current_app
from app.utils.process_book_file import process_book_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BookCache:
    CACHE_DURATION = timedelta(hours=24)

    @staticmethod
    def get_cached_books(category=None, limit=10):
        """Get books from cache/database"""
        try:
            query = Book.query.filter(Book.accessible_without_login == True)
            
            if category:
                query = query.filter(Book.category == category)
            
            books = query.order_by(Book.created_at.desc()).limit(limit).all()
            logger.info(f"Retrieved {len(books)} books for category {category}")
            return books
            
        except Exception as e:
            logger.error(f"Error getting cached books: {str(e)}")
            return []

    @staticmethod
    def cache_book(book_data):
        """Cache a book in the database"""
        try:
            if not book_data.get('title') or not book_data.get('source') or not book_data.get('source_id'):
                logger.warning(f"Invalid book data: {book_data}")
                return None

            existing_book = Book.query.filter_by(
                source=book_data['source'],
                source_id=book_data['source_id']
            ).first()

            if not existing_book:
                book = Book(
                    title=book_data.get('title', 'Unknown'),
                    author=book_data.get('author', 'Unknown'),
                    description=book_data.get('description', ''),
                    cover_url=book_data.get('cover', ''),
                    source=book_data.get('source', ''),
                    source_id=book_data.get('source_id', ''),
                    source_url=book_data.get('link', ''),
                    content=book_data.get('content', ''),
                    category=book_data.get('category', 'Other'),
                    language=book_data.get('language', 'en'),
                    file_type=book_data.get('file_type', ''),
                    accessible_without_login=True,
                    created_at=datetime.utcnow(),
                    user_id=1  # Set a default user ID or handle this differently
                )
                db.session.add(book)
                db.session.commit()
                logger.info(f"Cached new book: {book.title}")
                return book
            
            logger.info(f"Book already exists: {existing_book.title}")
            return existing_book
            
        except Exception as e:
            logger.error(f"Error caching book: {str(e)}")
            db.session.rollback()
            return None

    @staticmethod
    def refresh_cache():
        """Refresh the book cache with new books from various sources"""
        try:
            from app.utils.scraper import (
                OpenLibraryScraper, GutenbergScraper, 
                InternetArchiveScraper, AnnasArchiveScraper
            )

            scrapers = [
                (OpenLibraryScraper, 'openlibrary'),
                (GutenbergScraper, 'gutenberg'),
                (InternetArchiveScraper, 'archive'),
                (AnnasArchiveScraper, 'annas_archive')
            ]

            categories = ['Fiction', 'Non-Fiction', 'Science', 'Technology', 'History']
            
            for scraper, source in scrapers:
                try:
                    logger.info(f"Fetching featured books from {source}")
                    featured_books = scraper.get_featured_books(limit=5)
                    for book in featured_books:
                        book['category'] = 'Featured'
                        book['source'] = source
                        BookCache.cache_book(book)

                    for category in categories:
                        logger.info(f"Fetching {category} books from {source}")
                        category_books = scraper.get_books_by_category(category, limit=3)
                        for book in category_books:
                            book['category'] = category
                            book['source'] = source
                            BookCache.cache_book(book)

                except Exception as e:
                    logger.error(f"Error refreshing cache for {source}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in refresh_cache: {str(e)}")

    @staticmethod
    def get_local_books(limit=10):
        """Get books from the local epub folder"""
        try:
            # Get books from the epub folder that were uploaded directly
            query = Book.query.filter(
                Book.file_path.isnot(None),
                Book.file_type == 'EPUB'
            )
            books = query.order_by(Book.created_at.desc()).limit(limit).all()
            logger.info(f"Retrieved {len(books)} local EPUB books")
            return books
        except Exception as e:
            logger.error(f"Error getting local books: {str(e)}")
            return []

    @staticmethod
    def cache_local_books():
        """Cache books from the local epub folder"""
        try:
            epub_folder = current_app.config['UPLOAD_FOLDER']
            for filename in os.listdir(epub_folder):
                if filename.lower().endswith('.epub'):
                    filepath = os.path.join(epub_folder, filename)
                    book_info = process_book_file(filepath)
                    
                    # Check if book already exists
                    existing_book = Book.query.filter_by(file_path=filepath).first()
                    if not existing_book:
                        book = Book(
                            title=book_info.get('title', filename),
                            author=book_info.get('author', 'Unknown'),
                            description=book_info.get('description', ''),
                            file_path=filepath,
                            file_type='EPUB',
                            total_pages=book_info.get('total_pages', 0),
                            category='Local',
                            accessible_without_login=True,
                            created_at=datetime.utcnow()
                        )
                        db.session.add(book)
            
            db.session.commit()
            logger.info("Local EPUB books cached successfully")
            
        except Exception as e:
            logger.error(f"Error caching local books: {str(e)}")
            db.session.rollback()