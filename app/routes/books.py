import os
from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for, make_response, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Book, ReadingProgress, Bookmark, Review
from app import db
from app.utils.file_handler import process_book_file, allowed_file
from app.utils.book_sources import BookSourceManager
from app.utils.content_fetcher import BookContentFetcher
from datetime import datetime
import logging
from typing import List
from app.utils.content_processor import ContentProcessor
import io

# Set up logger
logger = logging.getLogger(__name__)

books_bp = Blueprint('books', __name__)

@books_bp.route('/books/upload', methods=['GET', 'POST'])
@login_required
def upload_book():
    if request.method == 'POST':
        if 'book_file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
            
        file = request.files['book_file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            book_info = process_book_file(filepath)
            
            book = Book(
                title=request.form.get('title', book_info.get('title', filename)),
                author=request.form.get('author', book_info.get('author', 'Unknown')),
                description=request.form.get('description', ''),
                file_path=filepath,
                file_type=os.path.splitext(filename)[1][1:].upper(),
                total_pages=book_info.get('total_pages', 0),
                user_id=current_user.id
            )
            
            db.session.add(book)
            db.session.commit()
            
            flash('Book uploaded successfully!', 'success')
            return redirect(url_for('books.view_book', book_id=book.id))
            
    return render_template('books/upload.html')

@books_bp.route('/books/<int:book_id>')
def view_book(book_id):
    book = Book.query.get_or_404(book_id)
    if current_user.is_authenticated:
        progress = ReadingProgress.query.filter_by(
            user_id=current_user.id,
            book_id=book_id
        ).first()
    else:
        progress = None
    return render_template('books/view.html', book=book, progress=progress)

@books_bp.route('/read/<string:source>/<string:book_id>')
def read_book(source, book_id):
    try:
        view_mode = request.args.get('view', 'paginated')
        
        # Get book details
        book = BookSourceManager.get_book_details(source, book_id)
        if not book:
            flash('Book not found', 'error')
            return redirect(url_for('main.index'))
        
        # Fetch book content
        content = BookContentFetcher.fetch_content({'source': source, 'source_id': book_id})
        if not content:
            flash('Unable to load book content', 'error')
            return redirect(url_for('books.book_details', source=source, book_id=book_id))
        
        if view_mode == 'full':
            # Return full book view
            return render_template('books/full_reader.html',
                                book=book,
                                content=content)
        
        # Process content into pages for paginated view
        pages = process_book_content(content)
        
        # Get reading progress
        progress = {
            'current_page': 1,
            'total_pages': len(pages)
        }
        
        return render_template('books/reader.html',
                             book=book,
                             content=pages,
                             progress=progress,
                             current_page=1,
                             total_pages=len(pages))
                             
    except Exception as e:
        logger.error(f"Error in read_book route: {str(e)}")
        flash('Error loading book. Please try again later.', 'error')
        return redirect(url_for('main.index'))

def process_book_content(content: str) -> List[str]:
    """Split book content into pages"""
    try:
        # Remove excess whitespace and split into paragraphs
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        
        # Group paragraphs into pages (roughly 2000 characters per page)
        pages = []
        current_page = []
        current_length = 0
        
        for paragraph in paragraphs:
            if current_length + len(paragraph) > 2000 and current_page:
                pages.append('\n'.join(current_page))
                current_page = []
                current_length = 0
            current_page.append(paragraph)
            current_length += len(paragraph)
        
        if current_page:
            pages.append('\n'.join(current_page))
        
        return pages
    except Exception as e:
        logger.error(f"Error processing book content: {e}")
        return [content]  # Return single page if processing fails

@books_bp.route('/api/books/<int:book_id>/progress', methods=['POST'])
@login_required
def update_progress(book_id):
    data = request.get_json()
    progress = ReadingProgress.query.filter_by(
        user_id=current_user.id,
        book_id=book_id
    ).first()
    
    if progress:
        progress.update_progress(
            current_page=data['current_page'],
            total_pages=data['total_pages']
        )
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 404

@books_bp.route('/api/books/<int:book_id>/bookmark', methods=['POST'])
@login_required
def add_bookmark(book_id):
    data = request.get_json()
    bookmark = Bookmark(
        user_id=current_user.id,
        book_id=book_id,
        page_number=data['page_number'],
        note=data.get('note', '')
    )
    db.session.add(bookmark)
    db.session.commit()
    return jsonify({'status': 'success', 'id': bookmark.id})

@books_bp.route('/api/books/<int:book_id>/review', methods=['POST'])
@login_required
def add_review(book_id):
    data = request.get_json()
    review = Review(
        user_id=current_user.id,
        book_id=book_id,
        rating=data['rating'],
        comment=data.get('comment', '')
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({'status': 'success', 'id': review.id})

@books_bp.route('/external-book/<string:source>/<path:book_id>')
def view_external_book(source, book_id):
    title = request.args.get('title', 'Unknown')
    author = request.args.get('author', 'Unknown')
    cover = request.args.get('cover', '')
    
    # Get book content
    content = None
    if source == 'openlibrary':
        content = OpenLibraryScraper.fetch_full_book_content(book_id)
    elif source == 'gutenberg':
        content = GutenbergScraper.fetch_full_book_content(book_id)
    
    book_info = {
        'title': title,
        'author': author,
        'cover': cover,
        'source': source,
        'id': book_id
    }
    
    return render_template('books/external_book.html', 
                         book=book_info,
                         content=content)

@books_bp.route('/add-to-library', methods=['POST'])
@login_required
def add_to_library():
    data = request.get_json()
    
    # Check if book already exists
    existing_book = Book.query.filter_by(
        source=data['source'],
        source_id=data['source_id'],
        user_id=current_user.id
    ).first()
    
    if existing_book:
        return jsonify({'status': 'error', 'message': 'Book already in library'})
    
    # Create new book
    book = Book(
        title=data['title'],
        author=data['author'],
        cover_image=data['cover'],
        source=data['source'],
        source_id=data['source_id'],
        user_id=current_user.id
    )
    
    db.session.add(book)
    db.session.commit()
    
    return jsonify({'status': 'success'})

@books_bp.route('/download/<int:book_id>/<string:format>')
@login_required
def download_book(book_id, format):
    try:
        book = Book.query.get_or_404(book_id)
        
        # Check if user has access to this book
        if not book.accessible_without_login and book.user_id != current_user.id:
            flash('You do not have permission to download this book.', 'error')
            return redirect(url_for('main.index'))
            
        if not book.content:
            flash('No content available for download.', 'error')
            return redirect(url_for('books.view_book', book_id=book.id))
            
        if format.lower() == 'txt':
            return download_txt(book)
        elif format.lower() == 'pdf':
            return download_pdf(book)
        else:
            flash('Invalid format specified.', 'error')
            return redirect(url_for('books.view_book', book_id=book.id))
            
    except Exception as e:
        print(f"Download error: {e}")
        flash('Error downloading book.', 'error')
        return redirect(url_for('books.view_book', book_id=book_id))

def download_txt(book):
    try:
        # Prepare content
        content = f"""
{book.title}
by {book.author}

{book.content}
        """.strip()
        
        # Create response
        response = make_response(content)
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename="{book.title}.txt"'
        
        return response
        
    except Exception as e:
        print(f"TXT download error: {e}")
        raise

def download_pdf(book):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Set up fonts
        pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        pdf.set_font('DejaVu', '', 12)
        
        # Add title
        pdf.set_font('DejaVu', '', 16)
        pdf.cell(0, 10, book.title, ln=True, align='C')
        
        # Add author
        pdf.set_font('DejaVu', '', 14)
        pdf.cell(0, 10, f"by {book.author}", ln=True, align='C')
        pdf.ln(10)
        
        # Add content
        pdf.set_font('DejaVu', '', 12)
        
        # Split content into lines and add to PDF
        content = book.content
        lines = content.split('\n')
        for line in lines:
            # Handle long lines by wrapping
            while len(line) > 0:
                chunk = line[:80]  # Adjust number based on font size and page width
                line = line[80:]
                pdf.multi_cell(0, 10, chunk)
        
        # Create in-memory buffer
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{book.title}.pdf"
        )
        
    except Exception as e:
        print(f"PDF download error: {e}")
        raise

@books_bp.route('/book/<string:source>/<string:book_id>')
def book_details(source, book_id):
    try:
        # Get book details
        book = BookSourceManager.get_book_details(source, book_id)
        if not book:
            flash('Book not found', 'error')
            return redirect(url_for('main.index'))
        
        # Get preview content (first few paragraphs)
        content = BookContentFetcher.fetch_content({'source': source, 'source_id': book_id})
        preview_content = None
        if content:
            # Process content to get a preview
            paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
            preview_content = '\n'.join(paragraphs[:3]) + '...'  # First 3 paragraphs
        
        return render_template('books/details.html',
                             book=book,
                             preview_content=preview_content)
                             
    except Exception as e:
        logger.error(f"Error in book_details route: {str(e)}")
        flash('Error loading book details. Please try again later.', 'error')
        return redirect(url_for('main.index'))

@books_bp.route('/api/books/progress', methods=['POST'])
@login_required
def save_progress():
    """Save reading progress for a book"""
    try:
        data = request.get_json()
        source = data.get('source')
        source_id = data.get('source_id')
        page = data.get('page')
        total_pages = data.get('total_pages')
        
        # Save progress to database
        progress = ReadingProgress.query.filter_by(
            user_id=current_user.id,
            source=source,
            source_id=source_id
        ).first()
        
        if not progress:
            progress = ReadingProgress(
                user_id=current_user.id,
                source=source,
                source_id=source_id,
                current_page=page,
                total_pages=total_pages
            )
            db.session.add(progress)
        else:
            progress.current_page = page
            progress.total_pages = total_pages
            
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error saving progress: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@books_bp.route('/summarize', methods=['GET', 'POST'])
@login_required
def summarize_book():
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file uploaded', 'error')
                return redirect(request.url)
                
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
                
            if file and allowed_file(file.filename):
                processor = ContentProcessor()
                
                # Extract text based on file type
                if file.filename.endswith('.pdf'):
                    text = processor.extract_text_from_pdf(file)
                elif file.filename.endswith('.epub'):
                    text = processor.extract_text_from_epub(file)
                elif file.filename.endswith('.txt'):
                    text = file.read().decode('utf-8')
                else:
                    flash('Unsupported file format', 'error')
                    return redirect(request.url)
                
                # Generate summary
                summary_data = processor.generate_summary(text)
                
                # Create PDF
                pdf_data = processor.create_summary_pdf(
                    summary_data, 
                    title=f"Summary of {file.filename}"
                )
                
                # Send PDF file
                return send_file(
                    io.BytesIO(pdf_data),
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f"summary_{file.filename}.pdf"
                )
                
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            flash('Error processing file', 'error')
            
    return render_template('books/summarize.html')
