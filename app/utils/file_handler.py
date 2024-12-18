import os
import PyPDF2
import ebooklib
from ebooklib import epub

ALLOWED_EXTENSIONS = {'pdf', 'epub'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_book_file(filepath):
    """Process uploaded book file and extract metadata"""
    file_ext = os.path.splitext(filepath)[1].lower()
    book_info = {}
    
    try:
        if file_ext == '.pdf':
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                book_info['total_pages'] = len(pdf_reader.pages)
                
                if pdf_reader.metadata:
                    book_info['title'] = pdf_reader.metadata.get('/Title', '')
                    book_info['author'] = pdf_reader.metadata.get('/Author', '')
                
        elif file_ext == '.epub':
            book = epub.read_epub(filepath)
            book_info['title'] = book.get_metadata('DC', 'title')[0][0]
            book_info['author'] = book.get_metadata('DC', 'creator')[0][0]
            book_info['total_pages'] = len(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
            
    except Exception as e:
        print(f"Error processing file: {e}")
        
    return book_info

def get_book_content(filepath, page_number):
    """Extract content from a specific page of the book"""
    file_ext = os.path.splitext(filepath)[1].lower()
    content = ""
    
    try:
        if file_ext == '.pdf':
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if 0 <= page_number < len(pdf_reader.pages):
                    content = pdf_reader.pages[page_number].extract_text()
                    
        elif file_ext == '.epub':
            book = epub.read_epub(filepath)
            documents = book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
            if 0 <= page_number < len(documents):
                content = documents[page_number].get_content().decode('utf-8')
                
    except Exception as e:
        print(f"Error extracting content: {e}")
        
    return content
