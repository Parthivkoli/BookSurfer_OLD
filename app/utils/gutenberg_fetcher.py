import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
import re
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class GutenbergAPI:
    BASE_URL = "https://www.gutenberg.org"
    MIRRORS = [
        "https://www.gutenberg.org",
        "http://www.gutenberg.org",
        "http://aleph.gutenberg.org",
        "http://manybooks.net/titles/",
    ]

    ENDPOINTS = {
        'top_books': '/browse/scores/top',
        'latest': '/ebooks/search/?sort_order=release_date',
        'most_downloaded': '/ebooks/search/?sort_order=downloads',
        'bookshelves': '/ebooks/bookshelf/',
    }

    @classmethod
    def get_book_formats(cls, book_id: str) -> Dict[str, str]:
        """Get all available formats for a book"""
        try:
            url = f"{cls.BASE_URL}/ebooks/{book_id}"
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                formats = {}
                
                # First try to get the high quality cover
                cover_patterns = [
                    f"{cls.BASE_URL}/cache/epub/{book_id}/pg{book_id}.cover.medium.jpg",
                    f"{cls.BASE_URL}/files/{book_id}/{book_id}-h/{book_id}-h-cover.jpg",
                    f"{cls.BASE_URL}/cache/epub/{book_id}/images/cover.jpg",
                ]
                
                # Test each cover URL until we find one that works
                for cover_url in cover_patterns:
                    try:
                        cover_response = requests.head(cover_url)
                        if cover_response.status_code == 200:
                            formats['cover'] = cover_url
                            break
                    except Exception:
                        continue
                
                # Find all download links
                for link in soup.select('table.files a'):
                    href = link.get('href', '')
                    text = link.get_text().lower()
                    
                    if 'epub' in text:
                        formats['epub'] = urljoin(cls.BASE_URL, href)
                    elif 'kindle' in text or '.mobi' in href:
                        formats['mobi'] = urljoin(cls.BASE_URL, href)
                    elif 'html' in text:
                        formats['html'] = urljoin(cls.BASE_URL, href)
                    elif 'text' in text or '.txt' in href:
                        formats['text'] = urljoin(cls.BASE_URL, href)
                    elif 'pdf' in text:
                        formats['pdf'] = urljoin(cls.BASE_URL, href)
                    elif ('cover' in text or '.jpg' in href or '.png' in href) and 'cover' not in formats:
                        formats['cover'] = urljoin(cls.BASE_URL, href)
                
                # If still no cover, use a default cover
                if 'cover' not in formats:
                    formats['cover'] = f"{cls.BASE_URL}/cache/epub/{book_id}/pg{book_id}.cover.small.jpg"
                
                return formats
        except Exception as e:
            logger.error(f"Error fetching book formats: {e}")
        return {}

    @classmethod
    def get_top_books(cls, limit: int = 8) -> List[Dict]:
        """Get top/featured books from Gutenberg"""
        try:
            url = f"{cls.BASE_URL}{cls.ENDPOINTS['most_downloaded']}"
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                books = []
                
                # Find all book entries
                for book_entry in soup.select('.booklink'):
                    try:
                        # Get book ID
                        link = book_entry.find('a', href=True)
                        if not link:
                            continue
                        book_id_match = re.search(r'/ebooks/(\d+)', link['href'])
                        if not book_id_match:
                            continue
                        
                        book_id = book_id_match.group(1)
                        
                        # Get title and author
                        title_elem = book_entry.find(class_='title')
                        author_elem = book_entry.find(class_='subtitle')
                        
                        title = title_elem.get_text().strip() if title_elem else 'Unknown Title'
                        author = author_elem.get_text().strip() if author_elem else 'Unknown Author'
                        
                        # More thorough author validation
                        invalid_authors = [
                            'Unknown Author', 'Anonymous', 'Unknown', 'Various', 
                            'N/A', '', 'None', 'Undefined', 'By Unknown Author',
                            'By Anonymous', 'Multiple Authors'
                        ]
                        
                        # Skip if author is in invalid list or contains "unknown"
                        if (author in invalid_authors or 
                            'unknown' in author.lower() or 
                            'anonymous' in author.lower() or
                            len(author) < 2):  # Skip very short author names
                            continue
                        
                        # Get cover URL
                        cover_url = f"{cls.BASE_URL}/cache/epub/{book_id}/pg{book_id}.cover.medium.jpg"
                        
                        # Verify cover exists
                        try:
                            cover_response = requests.head(cover_url)
                            if cover_response.status_code != 200:
                                continue  # Skip books without covers
                        except Exception:
                            continue
                        
                        books.append({
                            'id': book_id,
                            'title': title,
                            'author': author,
                            'cover_url': cover_url,
                            'source': 'gutenberg'
                        })
                        
                        if len(books) >= limit:
                            break
                            
                    except Exception as e:
                        logger.error(f"Error processing book entry: {e}")
                        continue
                
                # If we don't have enough books, try the latest books endpoint
                if len(books) < limit:
                    latest_url = f"{cls.BASE_URL}{cls.ENDPOINTS['latest']}"
                    try:
                        response = requests.get(latest_url)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            for book_entry in soup.select('.booklink'):
                                # (Same book processing logic as above)
                                # ... (Copy the same book processing logic here)
                                if len(books) >= limit:
                                    break
                    except Exception as e:
                        logger.error(f"Error fetching latest books: {e}")
                
                return books[:limit]
                
        except Exception as e:
            logger.error(f"Error fetching top books: {e}")
        return []

    @classmethod
    def get_bookshelf_books(cls, bookshelf: str, limit: int = 20) -> List[Dict]:
        """Get books from a specific bookshelf/category"""
        try:
            url = f"{cls.BASE_URL}/ebooks/bookshelf/{bookshelf}"
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                books = []
                
                for item in soup.select('.booklink')[:limit]:
                    link = item.find('a')
                    if link:
                        book_id = re.search(r'/ebooks/(\d+)', link['href'])
                        if book_id:
                            book_id = book_id.group(1)
                            book_formats = cls.get_book_formats(book_id)
                            
                            books.append({
                                'id': book_id,
                                'title': link.get_text().strip(),
                                'formats': book_formats,
                                'cover_url': book_formats.get('cover', ''),
                                'epub_url': book_formats.get('epub', ''),
                                'html_url': book_formats.get('html', ''),
                                'text_url': book_formats.get('text', ''),
                                'source': 'gutenberg',
                                'category': bookshelf
                            })
                
                return books
        except Exception as e:
            logger.error(f"Error fetching bookshelf books: {e}")
        return []

    @classmethod
    def get_book_content(cls, book_id: str, format: str = 'text') -> Optional[str]:
        """Get the full content of a book in specified format"""
        try:
            formats = cls.get_book_formats(book_id)
            if format in formats:
                response = requests.get(formats[format])
                if response.status_code == 200:
                    if format == 'html':
                        soup = BeautifulSoup(response.text, 'html.parser')
                        # Remove navigation and header elements
                        for elem in soup.select('pre'):
                            elem.decompose()
                        return str(soup)
                    return response.text
        except Exception as e:
            logger.error(f"Error fetching book content: {e}")
        return None

    @classmethod
    def search_books(cls, query: str, limit: int = 20) -> List[Dict]:
        """Search for books"""
        try:
            url = f"{cls.BASE_URL}/ebooks/search/?query={query}&submit_search=Go%21"
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                books = []
                
                for item in soup.select('.booklink')[:limit]:
                    link = item.find('a')
                    if link:
                        book_id = re.search(r'/ebooks/(\d+)', link['href'])
                        if book_id:
                            book_id = book_id.group(1)
                            book_formats = cls.get_book_formats(book_id)
                            
                            books.append({
                                'id': book_id,
                                'title': link.get_text().strip(),
                                'formats': book_formats,
                                'cover_url': book_formats.get('cover', ''),
                                'epub_url': book_formats.get('epub', ''),
                                'html_url': book_formats.get('html', ''),
                                'text_url': book_formats.get('text', ''),
                                'source': 'gutenberg'
                            })
                
                return books
        except Exception as e:
            logger.error(f"Error searching books: {e}")
        return []

    @classmethod
    def get_category_titles(cls, category: str, limit: int = 12) -> List[Dict]:
        """Get just titles without fetching covers"""
        try:
            url = f"{cls.BASE_URL}/ebooks/bookshelf/{category}"
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
            logger.error(f"Error fetching category titles: {e}")
        return [] 

    @classmethod
    def get_all_bookshelves(cls) -> List[Dict]:
        """Get all available bookshelves/categories from Gutenberg"""
        try:
            url = f"{cls.BASE_URL}/ebooks/bookshelf/"
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                bookshelves = []
                
                # Find all bookshelf links
                for link in soup.select('ul.results a'):
                    href = link.get('href', '')
                    if '/ebooks/bookshelf/' in href:
                        shelf_id = href.split('/')[-1]
                        name = link.get_text().strip()
                        book_count_text = link.find_next('span', class_='count')
                        book_count = 0
                        if book_count_text:
                            count_match = re.search(r'\((\d+)\)', book_count_text.text)
                            if count_match:
                                book_count = int(count_match.group(1))
                        
                        bookshelves.append({
                            'id': shelf_id,
                            'name': name,
                            'book_count': book_count,
                            'url': urljoin(cls.BASE_URL, href)
                        })
                
                # Sort by book count (most popular first)
                return sorted(bookshelves, key=lambda x: x['book_count'], reverse=True)
        except Exception as e:
            logger.error(f"Error fetching bookshelves: {e}")
        return [] 

    @classmethod
    def get_book_info(cls, book_id: str) -> Optional[Dict]:
        """Get basic book information"""
        try:
            url = f"{cls.BASE_URL}/ebooks/{book_id}"
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
            logger.error(f"Error fetching book info: {e}")
        return None

    @classmethod
    def get_all_categories(cls) -> List[Dict]:
        """Get all available categories"""
        try:
            url = f"{cls.BASE_URL}/browse/scores/top"
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                categories = []
                
                for link in soup.select('.category a'):
                    href = link.get('href', '')
                    if '/browse/scores/' in href:
                        category_id = href.split('/')[-1]
                        categories.append({
                            'id': category_id,
                            'name': link.get_text().strip(),
                            'url': urljoin(cls.BASE_URL, href)
                        })
                
                return categories
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
        return [] 