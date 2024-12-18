from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import Book
from app.extensions import db
from app.utils.scraper import (
    OpenLibraryScraper, GutenbergScraper, 
    InternetArchiveScraper, StandardEbooksScraper, AnnasArchiveScraper
)
from app.utils.summarizer import TextSummarizer
from app.utils.google_books_api import GoogleBooksAPI

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/books/search', methods=['GET'])
def search_books():
    query = request.args.get('query', '')
    source = request.args.get('source', 'all')
    
    results = []
    
    # First priority: Open source books
    if source in ['all', 'archive']:
        archive_books = InternetArchiveScraper.search_books(query)
        for book in archive_books:
            book['source'] = 'archive'
            book['can_read_online'] = True
            results.append(book)
            
    if source in ['all', 'gutenberg']:
        gutenberg_books = GutenbergScraper.search_books(query)
        for book in gutenberg_books:
            book['source'] = 'gutenberg'
            book['can_read_online'] = True
            results.append(book)
            
    if source in ['all', 'standard']:
        standard_books = StandardEbooksScraper.search_books(query)
        for book in standard_books:
            book['source'] = 'standard'
            book['can_read_online'] = True
            results.append(book)
    
    # Second priority: OpenLibrary
    if source in ['all', 'openlibrary']:
        openlibrary_books = OpenLibraryScraper.search_books(query)
        for book in openlibrary_books:
            book['source'] = 'openlibrary'
            book['can_read_online'] = book.get('is_public_domain', False)
            results.append(book)
    
    # Add Anna's Archive
    if source in ['all', 'annas_archive']:
        annas_books = AnnasArchiveScraper.search_books(query)
        for book in annas_books:
            book['source'] = 'annas_archive'
            book['can_read_online'] = True
            results.append(book)
    
    # Sort results: Open source books first, then by relevance
    results.sort(key=lambda x: (
        not x.get('can_read_online', False),  # False sorts after True
        not x.get('is_public_domain', False),  # False sorts after True
        -x.get('relevance_score', 0)  # Higher scores first
    ))
    
    return jsonify({'results': results})

@api_bp.route('/api/books/save', methods=['POST'])
@login_required
def save_book():
    try:
        data = request.get_json()
        source = data.get('source')
        book_id = data.get('book_id')
        
        # Check if book already exists
        existing_book = Book.query.filter_by(
            source=source,
            source_id=book_id,
            user_id=current_user.id
        ).first()
        
        if existing_book:
            return jsonify({
                'status': 'error',
                'message': 'Book already exists in your library'
            }), 409
            
        # Fetch full book content based on source
        content = None
        if source == 'openlibrary':
            content = OpenLibraryScraper.fetch_full_book_content(book_id)
        elif source == 'gutenberg':
            content = GutenbergScraper.fetch_full_book_content(book_id)
        elif source == 'archive':
            content = InternetArchiveScraper.fetch_full_book_content(book_id)
        elif source == 'standard':
            content = StandardEbooksScraper.fetch_full_book_content(book_id)
            
        if not content:
            return jsonify({
                'status': 'error',
                'message': 'Could not fetch book content'
            }), 404
            
        # Generate summary if content is available
        summary = None
        if content.get('content'):
            summarizer = TextSummarizer()
            summary = summarizer.summarize(
                content['content'][:5000],  # Summarize first 5000 chars
                method='extractive',
                length='medium'
            )
        
        # Create new book record
        book = Book(
            title=content.get('title', data.get('title', 'Unknown')),
            author=content.get('author', data.get('author', 'Unknown')),
            content=content.get('content'),
            summary=summary,
            cover_url=content.get('cover_url', data.get('cover_url')),
            source_url=content.get('source_url'),
            source=source,
            source_id=book_id,
            user_id=current_user.id,
            category=data.get('category', 'Public'),
            accessible_without_login=data.get('accessible_without_login', True)
        )
        
        db.session.add(book)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Book saved successfully',
            'book': book.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/api/books/batch-save', methods=['POST'])
@login_required
def batch_save_books():
    try:
        data = request.get_json()
        books = data.get('books', [])
        results = []
        
        for book_data in books:
            source = book_data.get('source')
            book_id = book_data.get('book_id')
            
            # Skip if book already exists
            if Book.query.filter_by(
                source=source,
                source_id=book_id,
                user_id=current_user.id
            ).first():
                results.append({
                    'book_id': book_id,
                    'status': 'skipped',
                    'message': 'Book already exists'
                })
                continue
                
            try:
                # Fetch and save book
                content = None
                if source == 'openlibrary':
                    content = OpenLibraryScraper.fetch_full_book_content(book_id)
                elif source == 'gutenberg':
                    content = GutenbergScraper.fetch_full_book_content(book_id)
                # ... add other sources as needed
                
                if content:
                    book = Book(
                        title=content.get('title', book_data.get('title', 'Unknown')),
                        author=content.get('author', book_data.get('author', 'Unknown')),
                        content=content.get('content'),
                        cover_url=content.get('cover_url'),
                        source_url=content.get('source_url'),
                        source=source,
                        source_id=book_id,
                        user_id=current_user.id
                    )
                    db.session.add(book)
                    results.append({
                        'book_id': book_id,
                        'status': 'success',
                        'message': 'Book saved successfully'
                    })
                else:
                    results.append({
                        'book_id': book_id,
                        'status': 'error',
                        'message': 'Could not fetch book content'
                    })
                    
            except Exception as e:
                results.append({
                    'book_id': book_id,
                    'status': 'error',
                    'message': str(e)
                })
                
        db.session.commit()
        return jsonify({
            'status': 'success',
            'results': results
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 