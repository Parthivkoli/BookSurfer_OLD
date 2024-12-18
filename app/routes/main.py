from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Book, ReadingProgress, Bookmark
from app.utils.api_client import OpenLibraryAPI, InternetArchiveAPI
# from app.utils.google_books_api import GoogleBooksAPI  # Comment out this line
from app.utils.scraper import OpenLibraryScraper, GutenbergScraper, GoodreadsScraper, StandardEbooksScraper, ManyBooksScraper, InternetArchiveScraper, SmashwordsScraper, NoteGPTScraper, AnnasArchiveScraper
from app.utils.summarizer import TextSummarizer
from app.extensions import db
import os
from werkzeug.utils import secure_filename
from app.utils.book_cache import BookCache
from app.utils.book_sources import BookSourceManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

# Corrected route registration for 'summarizer'
@main_bp.route('/summarizer', methods=['GET', 'POST'])
def summarizer():
    if request.method == 'POST':
        try:
            text = request.form.get('text', '').strip()
            uploaded_file = request.files.get('file')
            
            # Handle file upload
            if uploaded_file and uploaded_file.filename:
                filename = secure_filename(uploaded_file.filename)
                file_ext = os.path.splitext(filename)[1].lower()
                
                if file_ext == '.txt':
                    text = uploaded_file.read().decode('utf-8')
                elif file_ext in ['.doc', '.docx']:
                    # Add docx handling if needed
                    from docx import Document
                    document = Document(uploaded_file)
                    text = '\n'.join([paragraph.text for paragraph in document.paragraphs])
                elif file_ext == '.pdf':
                    # Add PDF handling if needed
                    import PyPDF2
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    text = ''
                    for page in pdf_reader.pages:
                        text += page.extract_text()
            
            if not text:
                flash('Please enter some text or upload a file to summarize.', 'error')
                return render_template('main/summarize.html')
                
            method = request.form.get('method', 'extractive')
            length = request.form.get('length', 'medium')
            
            summarizer = TextSummarizer()
            summary = summarizer.summarize(
                text=text,
                method=method,
                length=length
            )
            
            if not summary:
                flash('Could not generate summary. Please try again.', 'error')
                return render_template('main/summarize.html', 
                                    original_text=text,
                                    method=method,
                                    length=length)
            
            return render_template('main/summarize.html', 
                                 original_text=text,
                                 summary=summary,
                                 method=method,
                                 length=length)
                                 
        except Exception as e:
            print(f"Summarization error: {e}")
            flash('An error occurred during summarization. Please try again.', 'error')
            return render_template('main/summarize.html')
    
    return render_template('main/summarize.html')

@main_bp.route('/')
def index():
    try:
        # Get only 8 featured books
        featured_books = BookSourceManager.get_featured_books(limit=8)
        
        # Get just book titles for categories (faster loading)
        categories = {
            'Fiction': BookSourceManager.get_category_titles('fiction', limit=12),
            'Non-Fiction': BookSourceManager.get_category_titles('non-fiction', limit=12),
            'Science Fiction': BookSourceManager.get_category_titles('science-fiction', limit=12),
            'Romance': BookSourceManager.get_category_titles('romance', limit=12),
            'Mystery': BookSourceManager.get_category_titles('mystery', limit=12),
        }
        
        return render_template('main/index.html',
                             featured_books=featured_books,
                             categories=categories)
                             
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        flash('Error loading books. Please try again later.', 'error')
        return render_template('main/index.html',
                             featured_books=[],
                             categories={})

@main_bp.route('/dashboard')
@login_required
def dashboard():
    user_books = Book.query.filter_by(user_id=current_user.id).all()
    reading_progress = ReadingProgress.query.filter_by(user_id=current_user.id).all()
    return render_template('main/dashboard.html', 
                         books=user_books, 
                         reading_progress=reading_progress)

@main_bp.route('/discover')
def discover():
    try:
        # Get all categories from Gutenberg
        all_categories = BookSourceManager.get_all_categories()
        
        # Initialize empty book lists for each category
        category_books = {}
        
        # Get first 12 books for each category
        for category in all_categories[:15]:  # Limit to top 15 categories
            books = BookSourceManager.get_category_titles(category['id'], limit=12)
            if books:  # Only add categories that have books
                category_books[category['name']] = books
        
        return render_template('main/discover.html', 
                             categories=category_books,
                             all_categories=all_categories)
    except Exception as e:
        logger.error(f"Error in discover route: {e}")
        flash('Error loading categories. Please try again later.', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    openlibrary_results = OpenLibraryScraper.search_books(query)
    gutenberg_results = GutenbergScraper.search_books(query)
    goodreads_results = GoodreadsScraper.search_books(query)
    annas_archive_results = AnnasArchiveScraper.search_books(query)

    # Combine results from all sources
    all_results = {
        'openlibrary': openlibrary_results,
        'gutenberg': gutenberg_results,
        'goodreads': goodreads_results,
        'annas_archive': annas_archive_results
    }
    return render_template('main/search_results.html', 
                         openlibrary_results=openlibrary_results,
                         gutenberg_results=gutenberg_results,
                         annas_archive_results=annas_archive_results,
                         all_results=all_results)

@main_bp.route('/book/bookmark', methods=['POST'])
def add_bookmark():
    data = request.get_json()
    book_id = data['bookId']
    page = data['page']
    bookmark = Bookmark(book_id=book_id, page=page, user_id=current_user.id)
    db.session.add(bookmark)
    db.session.commit()
    return jsonify({'status': 'success'})

@main_bp.route('/categories')
def categories():
    try:
        # Get all categories from Gutenberg
        all_categories = BookSourceManager.get_all_categories()
        
        # Get a sample of books for each category
        categories_with_books = {}
        for category in all_categories[:8]:  # Limit to top 8 categories
            books = BookSourceManager.get_category_titles(category['id'], limit=4)
            if books:
                categories_with_books[category['name']] = {
                    'books': books,
                    'total': category['book_count'],
                    'id': category['id'],
                    'url': category['url']
                }
        
        return render_template('main/categories.html', 
                             categories=categories_with_books)
    except Exception as e:
        logger.error(f"Error in categories route: {e}")
        flash('Error loading categories. Please try again later.', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/browse/<category>')
def browse(category):
    try:
        books = []
        
        # Get books based on category
        if category == 'featured':
            gutenberg_books = GutenbergScraper.get_featured_books(limit=4)
            standard_books = StandardEbooksScraper.get_featured_books(limit=4)
            archive_books = InternetArchiveScraper.get_featured_books(limit=4)
            
            books.extend(gutenberg_books)
            books.extend(standard_books)
            books.extend(archive_books)
            
        elif category == 'trending':
            gutenberg_trending = GutenbergScraper.get_trending_books(limit=4)
            standard_trending = StandardEbooksScraper.get_trending_books(limit=4)
            archive_trending = InternetArchiveScraper.get_trending_books(limit=4)
            
            books.extend(gutenberg_trending)
            books.extend(standard_trending)
            books.extend(archive_trending)
            
        else:
            # Get category-specific books
            gutenberg_cat = GutenbergScraper.get_books_by_category(category, limit=4)
            standard_cat = StandardEbooksScraper.get_books_by_category(category, limit=4)
            archive_cat = InternetArchiveScraper.get_books_by_category(category, limit=4)
            
            books.extend(gutenberg_cat)
            books.extend(standard_cat)
            books.extend(archive_cat)

        return render_template('main/browse.html',
                             category=category.title(),
                             books=books)
                             
    except Exception as e:
        print(f"Error in browse route: {e}")
        flash('Error loading books. Please try again later.', 'error')
        return render_template('main/browse.html',
                             category=category.title(),
                             books=[])
