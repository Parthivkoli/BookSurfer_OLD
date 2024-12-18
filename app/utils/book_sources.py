import requests
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import json
import os
from flask import current_app
import re
from urllib.parse import urljoin
from app.utils.gutenberg_fetcher import GutenbergAPI
from app.utils.archive_fetcher import ArchiveAPI

logger = logging.getLogger(__name__)

class BookSource:
    @staticmethod
    def handle_request_error(e: Exception, source: str) -> None:
        logger.error(f"Error fetching from {source}: {str(e)}")

class GutenbergSource(BookSource):
    BASE_URL = "https://gutenberg.org/ebooks"
    API_URL = "https://gutendex.com/books"

    @classmethod
    def get_featured_books(cls, limit: int = 10) -> List[Dict]:
        try:
            from app.utils.gutenberg_fetcher import GutenbergAPI
            return GutenbergAPI.get_top_books(limit=limit)
        except Exception as e:
            cls.handle_request_error(e, "Gutenberg")
        return []

    @classmethod
    def get_category_titles(cls, category: str, limit: int = 12) -> List[Dict]:
        """Get just titles without fetching covers"""
        try:
            url = f"{cls.BASE_URL}/bookshelf/{category}"
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                books = []
                
                for link in soup.select('.booklink a')[:limit]:
                    book_id = re.search(r'/ebooks/(\d+)', link['href'])
                    if book_id:
                        text = link.get_text()
                        author = ''
                        title = text
                        
                        by_match = re.search(r'^(.*?)\s+by\s+(.*)$', text)
                        if by_match:
                            title = by_match.group(1).strip()
                            author = by_match.group(2).strip()
                        
                        books.append({
                            'id': book_id.group(1),
                            'title': title,
                            'author': author,
                            'source': 'gutenberg'
                        })
                
                return sorted(books, key=lambda x: x['title'])
        except Exception as e:
            cls.handle_request_error(e, "Gutenberg category")
        return []

    @classmethod
    def get_book_info(cls, book_id: str) -> Optional[Dict]:
        """Get basic book information"""
        try:
            url = f"{cls.BASE_URL}/{book_id}"
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Get title and author
                title_elem = soup.select_one('h1')
                title = title_elem.get_text().strip() if title_elem else 'Unknown Title'
                
                author_elem = soup.select_one('.author')
                author = author_elem.get_text().strip() if author_elem else 'Unknown Author'
                
                # Get cover URL
                cover_url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.cover.medium.jpg"
                
                # Get description
                description_elem = soup.select_one('.description')
                description = description_elem.get_text().strip() if description_elem else ''
                
                return {
                    'title': title,
                    'author': author,
                    'cover_url': cover_url,
                    'description': description,
                    'source': 'gutenberg',
                    'source_id': book_id,
                    'language': 'en'
                }
        except Exception as e:
            cls.handle_request_error(e, "Gutenberg book info")
        return None

    @classmethod
    def get_book_details(cls, book_id: str) -> Optional[Dict]:
        """Get detailed book information"""
        try:
            # First try to get from API
            api_url = f"{cls.API_URL}?ids={book_id}"
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    book = data['results'][0]
                    return {
                        'title': book['title'],
                        'author': book['authors'][0]['name'] if book['authors'] else 'Unknown Author',
                        'cover_url': f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.cover.medium.jpg",
                        'description': book.get('description', ''),
                        'language': book.get('languages', ['en'])[0],
                        'source': 'gutenberg',
                        'source_id': book_id,
                        'formats': book.get('formats', {})
                    }
            
            # Fallback to scraping if API fails
            return cls.get_book_info(book_id)
            
        except Exception as e:
            cls.handle_request_error(e, "Gutenberg book details")
        return None

    @classmethod
    def get_books_by_category(cls, category: str, limit: int = 10) -> List[Dict]:
        try:
            from app.utils.gutenberg_fetcher import GutenbergAPI
            # Map categories to Gutenberg bookshelves
            category_map = {
                'fiction': 'fiction',
                'non-fiction': 'non-fiction',
                'science-fiction': 'science-fiction',
                'romance': 'romance',
                'mystery': 'detective-fiction',
                'technology': 'technology'
            }
            gutenberg_category = category_map.get(category.lower(), category.lower())
            return GutenbergAPI.get_bookshelf_books(gutenberg_category, limit=limit)
        except Exception as e:
            cls.handle_request_error(e, "Gutenberg")
        return []

    @classmethod
    def get_all_categories(cls) -> List[Dict]:
        """Get all available categories with metadata"""
        try:
            from app.utils.gutenberg_fetcher import GutenbergAPI
            return GutenbergAPI.get_all_bookshelves()
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return []

class InternetArchiveSource(BookSource):
    BASE_URL = "https://archive.org"
    API_URL = "https://archive.org/advancedsearch.php"

    @classmethod
    def get_featured_books(cls, limit: int = 10) -> List[Dict]:
        try:
            params = {
                'q': 'mediatype:texts AND format:pdf',
                'fl[]': ['title', 'creator', 'identifier', 'language'],
                'sort[]': ['downloads desc'],
                'rows': limit,
                'page': 1,
                'output': 'json'
            }
            response = requests.get(cls.API_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                books = []
                for doc in data['response']['docs']:
                    books.append({
                        'title': doc.get('title', 'Unknown Title'),
                        'author': doc.get('creator', 'Unknown Author'),
                        'cover_url': f"{cls.BASE_URL}/services/img/{doc['identifier']}",
                        'source': 'archive',
                        'source_id': doc['identifier'],
                        'language': doc.get('language', ['en'])[0]
                    })
                return books
        except Exception as e:
            cls.handle_request_error(e, "Internet Archive")
        return []

class StandardEbooksSource(BookSource):
    BASE_URL = "https://standardebooks.org"
    
    @classmethod
    def get_featured_books(cls, limit: int = 10) -> List[Dict]:
        try:
            response = requests.get(f"{cls.BASE_URL}/ebooks/")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                books = []
                for item in soup.select('.ebook-list li')[:limit]:
                    title_elem = item.select_one('.title')
                    author_elem = item.select_one('.author')
                    cover_elem = item.select_one('img')
                    
                    if title_elem and author_elem:
                        books.append({
                            'title': title_elem.text.strip(),
                            'author': author_elem.text.strip(),
                            'cover_url': f"{cls.BASE_URL}{cover_elem['src']}" if cover_elem else '',
                            'source': 'standard',
                            'source_id': title_elem.find_parent('a')['href'].split('/')[-1],
                            'language': 'en'
                        })
                return books
        except Exception as e:
            cls.handle_request_error(e, "Standard Ebooks")
        return []

class BookSourceManager:
    SOURCES = {
        'gutenberg': GutenbergAPI,
        'archive': ArchiveAPI
    }

    @classmethod
    def get_featured_books(cls, limit: int = 8) -> List[Dict]:
        """Get featured books from all sources"""
        books = []
        per_source = limit // len(cls.SOURCES)  # Split limit between sources
        
        for source in cls.SOURCES.values():
            try:
                source_books = source.get_top_books(limit=per_source)
                books.extend(source_books)
            except Exception as e:
                logger.error(f"Error fetching from source {source.__name__}: {str(e)}")
        
        # Sort by downloads/popularity if available
        books.sort(key=lambda x: x.get('downloads', 0), reverse=True)
        return books[:limit]

    @classmethod
    def get_category_titles(cls, category: str, limit: int = 12) -> List[Dict]:
        """Get just titles and basic info without covers for faster loading"""
        try:
            return cls.SOURCES['gutenberg'].get_category_titles(category, limit=limit)
        except Exception as e:
            logger.error(f"Error fetching category titles: {e}")
            return [] 

    @classmethod
    def get_book_details(cls, source: str, book_id: str) -> Optional[Dict]:
        """Get detailed information about a specific book"""
        try:
            if source not in cls.SOURCES:
                logger.error(f"Invalid source: {source}")
                return None
            
            source_class = cls.SOURCES[source]
            
            # Try get_book_details first
            if hasattr(source_class, 'get_book_details'):
                book = source_class.get_book_details(book_id)
                if book:
                    return book
            
            # Fallback to get_book_info
            if hasattr(source_class, 'get_book_info'):
                book = source_class.get_book_info(book_id)
                if book:
                    return {
                        'title': book.get('title', 'Unknown Title'),
                        'author': book.get('author', 'Unknown Author'),
                        'cover_url': book.get('cover_url', ''),
                        'source': source,
                        'source_id': book_id,
                        'description': book.get('description', ''),
                        'language': book.get('language', 'en')
                    }
            
            return None
        except Exception as e:
            logger.error(f"Error getting book details: {e}")
            return None

    @classmethod
    def get_all_categories(cls) -> List[Dict]:
        """Get all available categories from all sources"""
        categories = []
        try:
            # Get Gutenberg categories
            gutenberg_categories = cls.SOURCES['gutenberg'].get_all_categories()
            categories.extend(gutenberg_categories)
            
            # Get Archive.org categories (if implemented)
            if hasattr(cls.SOURCES['archive'], 'get_all_categories'):
                archive_categories = cls.SOURCES['archive'].get_all_categories()
                categories.extend(archive_categories)
            
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
        
        return categories