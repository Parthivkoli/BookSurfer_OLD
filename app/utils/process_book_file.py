import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os

def process_book_file(filepath):
    """Process an EPUB file and extract metadata"""
    try:
        book = epub.read_epub(filepath)
        
        # Extract metadata
        title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else os.path.basename(filepath)
        author = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else 'Unknown'
        description = book.get_metadata('DC', 'description')[0][0] if book.get_metadata('DC', 'description') else ''
        
        # Get total pages (approximate by counting content files)
        total_pages = len(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
        
        # Extract cover image if available
        cover_image = None
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_COVER:
                cover_image = item
                break
        
        return {
            'title': title,
            'author': author,
            'description': description,
            'total_pages': total_pages,
            'cover_image': cover_image
        }
        
    except Exception as e:
        print(f"Error processing EPUB file: {e}")
        return {
            'title': os.path.basename(filepath),
            'author': 'Unknown',
            'description': '',
            'total_pages': 0,
            'cover_image': None
        } 