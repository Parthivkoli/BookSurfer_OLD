import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
import re
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class ArchiveAPI:
    BASE_URL = "https://archive.org"
    API_URL = "https://archive.org/advancedsearch.php"
    
    @classmethod
    def get_top_books(cls, limit: int = 8) -> List[Dict]:
        """Get top/featured books from Archive.org"""
        try:
            # Use advanced search API to get popular public domain books
            params = {
                'q': 'mediatype:texts AND collection:(gutenberg) AND !collection:(test_collection)',
                'fl[]': ['identifier', 'title', 'creator', 'downloads', 'imagecount'],
                'sort[]': ['downloads desc'],
                'rows': limit * 2,  # Get more to filter
                'page': 1,
                'output': 'json'
            }
            
            response = requests.get(cls.API_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                books = []
                
                for doc in data.get('response', {}).get('docs', []):
                    try:
                        identifier = doc.get('identifier')
                        creator = doc.get('creator', ['Unknown Author'])[0]
                        
                        # Skip books with unknown authors
                        invalid_authors = [
                            'Unknown Author', 'Anonymous', 'Unknown', 'Various',
                            'N/A', '', 'None', 'Undefined', 'Multiple Authors'
                        ]
                        
                        if (creator in invalid_authors or
                            'unknown' in creator.lower() or
                            'anonymous' in creator.lower() or
                            len(creator) < 2):
                            continue
                        
                        # Get cover URL
                        cover_url = f"{cls.BASE_URL}/services/img/{identifier}"
                        
                        # Verify cover exists
                        try:
                            cover_response = requests.head(cover_url)
                            if cover_response.status_code != 200:
                                continue
                        except Exception:
                            continue
                        
                        books.append({
                            'id': identifier,
                            'title': doc.get('title', 'Unknown Title'),
                            'author': creator,
                            'cover_url': cover_url,
                            'source': 'archive',
                            'downloads': doc.get('downloads', 0),
                            'pages': doc.get('imagecount', 0)
                        })
                        
                        if len(books) >= limit:
                            break
                            
                    except Exception as e:
                        logger.error(f"Error processing archive book: {e}")
                        continue
                
                return books[:limit]
                
        except Exception as e:
            logger.error(f"Error fetching archive books: {e}")
        return []

    @classmethod
    def get_book_details(cls, book_id: str) -> Optional[Dict]:
        """Get detailed information about a specific book"""
        try:
            metadata_url = f"{cls.BASE_URL}/metadata/{book_id}"
            response = requests.get(metadata_url)
            
            if response.status_code == 200:
                data = response.json()
                metadata = data.get('metadata', {})
                
                return {
                    'id': book_id,
                    'title': metadata.get('title', 'Unknown Title'),
                    'author': metadata.get('creator', 'Unknown Author'),
                    'cover_url': f"{cls.BASE_URL}/services/img/{book_id}",
                    'description': metadata.get('description', ''),
                    'language': metadata.get('language', ['en'])[0],
                    'publication_year': metadata.get('date', ''),
                    'publisher': metadata.get('publisher', ''),
                    'source': 'archive',
                    'formats': {
                        'pdf': f"{cls.BASE_URL}/download/{book_id}/{book_id}.pdf",
                        'epub': f"{cls.BASE_URL}/download/{book_id}/{book_id}.epub",
                        'text': f"{cls.BASE_URL}/download/{book_id}/{book_id}_djvu.txt",
                    }
                }
                
        except Exception as e:
            logger.error(f"Error fetching archive book details: {e}")
        return None

    @classmethod
    def get_book_content(cls, book_id: str) -> Optional[str]:
        """Get the book content in text format"""
        try:
            # Try to get the DjVu text version first
            text_url = f"{cls.BASE_URL}/download/{book_id}/{book_id}_djvu.txt"
            response = requests.get(text_url)
            
            if response.status_code == 200:
                return response.text
                
            # Fallback to OCR text if available
            ocr_url = f"{cls.BASE_URL}/download/{book_id}/{book_id}_djvu.xml"
            response = requests.get(ocr_url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'xml')
                text = ' '.join([p.get_text() for p in soup.find_all('PARAGRAPH')])
                return text
                
        except Exception as e:
            logger.error(f"Error fetching archive book content: {e}")
        return None

    @classmethod
    def search_books(cls, query: str, limit: int = 20) -> List[Dict]:
        """Search for books"""
        try:
            params = {
                'q': f'mediatype:texts AND (title:({query}) OR creator:({query}))',
                'fl[]': ['identifier', 'title', 'creator', 'downloads', 'imagecount'],
                'sort[]': ['downloads desc'],
                'rows': limit,
                'output': 'json'
            }
            
            response = requests.get(cls.API_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                books = []
                
                for doc in data.get('response', {}).get('docs', []):
                    books.append({
                        'id': doc.get('identifier'),
                        'title': doc.get('title', 'Unknown Title'),
                        'author': doc.get('creator', ['Unknown Author'])[0],
                        'cover_url': f"{cls.BASE_URL}/services/img/{doc.get('identifier')}",
                        'source': 'archive',
                        'downloads': doc.get('downloads', 0)
                    })
                
                return books
                
        except Exception as e:
            logger.error(f"Error searching archive books: {e}")
        return [] 