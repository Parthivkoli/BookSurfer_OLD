import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, quote
from typing import List, Dict, Optional

# OpenLibrary Scraper
class OpenLibraryScraper:
    BASE_URL = 'https://openlibrary.org'

    @staticmethod
    def _delay():
        time.sleep(1)  # Add 1 second delay between requests

    @classmethod
    def search_books(cls, query):
        cls._delay()  # Add delay before request
        search_url = f'{cls.BASE_URL}/search.json?q={query}'
        try:
            response = requests.get(search_url)
            if response.status_code == 200:
                data = response.json()
                books = []
                for doc in data.get('docs', []):
                    cover = f'https://covers.openlibrary.org/b/id/{doc.get("cover_i", "")}-L.jpg' if doc.get('cover_i') else None
                    if cover and "nophoto" not in cover:  # Ensuring valid cover images
                        books.append({
                            'title': doc.get('title', 'Unknown'),
                            'author': ', '.join(doc.get('author_name', ['Unknown'])),
                            'cover': cover,
                            'link': f'{OpenLibraryScraper.BASE_URL}/works/{doc.get("key")}',
                            'source': 'openlibrary'
                        })
                return books
        except Exception as e:
            print(f"Error in OpenLibraryScraper: {e}")
        return []

    @staticmethod
    def fetch_book_content(work_key):
        book_url = f'{OpenLibraryScraper.BASE_URL}/works/{work_key}.json'
        try:
            response = requests.get(book_url)
            if response.status_code == 200:
                data = response.json()
                return data.get('description', {}).get('value', 'No content available')
        except Exception as e:
            print(f"Error fetching book content from OpenLibrary: {e}")
        return None

    @staticmethod
    def fetch_full_book_content(work_key):
        try:
            # First try to get the Internet Archive ID
            work_url = f'{OpenLibraryScraper.BASE_URL}/works/{work_key}.json'
            response = requests.get(work_url)
            if response.status_code == 200:
                work_data = response.json()
                ia_id = work_data.get('ocaid')  # Internet Archive ID
                
                if ia_id:
                    # Try different formats in order of preference
                    formats = [
                        f'https://archive.org/download/{ia_id}/{ia_id}_djvu.txt',  # DjVu text
                        f'https://archive.org/download/{ia_id}/{ia_id}.txt',       # Plain text
                        f'https://archive.org/download/{ia_id}/{ia_id}.pdf'        # PDF
                    ]
                    
                    for format_url in formats:
                        try:
                            content_response = requests.get(format_url)
                            if content_response.status_code == 200:
                                return {
                                    'content': content_response.text,
                                    'title': work_data.get('title', 'Unknown'),
                                    'author': work_data.get('authors', [{'name': 'Unknown'}])[0].get('name'),
                                    'cover_url': f'https://covers.openlibrary.org/b/id/{work_data.get("covers", [""])[0]}-L.jpg',
                                    'source_url': f'{OpenLibraryScraper.BASE_URL}/works/{work_key}'
                                }
                        except Exception as e:
                            print(f"Error fetching format {format_url}: {e}")
                            continue
                
                # Fallback to description if full text not available
                return {
                    'content': work_data.get('description', {}).get('value', 'No content available'),
                    'title': work_data.get('title', 'Unknown'),
                    'author': work_data.get('authors', [{'name': 'Unknown'}])[0].get('name'),
                    'cover_url': f'https://covers.openlibrary.org/b/id/{work_data.get("covers", [""])[0]}-L.jpg',
                    'source_url': f'{OpenLibraryScraper.BASE_URL}/works/{work_key}'
                }
        except Exception as e:
            print(f"Error in OpenLibrary full content fetch: {e}")
        return None

    @classmethod
    def get_featured_books(cls, limit=5):
        """Get featured books from OpenLibrary"""
        try:
            # Search for popular books
            search_url = f'{cls.BASE_URL}/search.json?q=popular&limit={limit}'
            response = requests.get(search_url)
            if response.status_code == 200:
                data = response.json()
                books = []
                for doc in data.get('docs', [])[:limit]:
                    cover = f'https://covers.openlibrary.org/b/id/{doc.get("cover_i", "")}-L.jpg' if doc.get('cover_i') else None
                    if cover and "nophoto" not in cover:
                        books.append({
                            'title': doc.get('title', 'Unknown'),
                            'author': ', '.join(doc.get('author_name', ['Unknown'])),
                            'cover': cover,
                            'source': 'openlibrary',
                            'source_id': doc.get('key').split('/')[-1],
                            'link': f'{cls.BASE_URL}{doc.get("key")}',
                            'language': 'en',
                            'can_read_online': True
                        })
                return books
        except Exception as e:
            logger.error(f"Error in OpenLibrary featured books: {e}")
        return []

    @classmethod
    def get_books_by_category(cls, category, limit=5):
        """Get books by category from OpenLibrary"""
        return cls.search_books(f"{category} books")[:limit]

# Gutenberg Scraper
class GutenbergScraper:
    BASE_URL = 'https://www.gutenberg.org'
    MIRROR_URL = 'https://www.gutenberg.org/cache/epub'

    @staticmethod
    def _delay():
        time.sleep(1)  # Add 1 second delay between requests

    @classmethod
    def search_books(cls, query, limit=10):
        """Search books with limit parameter"""
        cls._delay()
        try:
            search_url = f'{cls.BASE_URL}/ebooks/search/?query={quote(query)}&submit_search=Go%21'
            response = requests.get(search_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                books = []
                
                for book_entry in soup.select('.booklink')[:limit]:
                    try:
                        # Extract book ID from the link
                        book_link = book_entry.select_one('a[href*="/ebooks/"]')
                        if not book_link:
                            continue
                        
                        book_id = re.search(r'/ebooks/(\d+)', book_link['href']).group(1)
                        
                        # Get title and clean it
                        title_elem = book_entry.select_one('.title')
                        title = title_elem.text.strip() if title_elem else 'Unknown'
                        title = re.sub(r'\s+', ' ', title)
                        
                        # Get author and clean it
                        author_elem = book_entry.select_one('.subtitle')
                        author = author_elem.text.strip() if author_elem else 'Unknown'
                        author = re.sub(r'\s+', ' ', author)
                        author = author.replace('by ', '')
                        
                        # Get cover image
                        cover_url = f'{cls.BASE_URL}/cache/epub/{book_id}/pg{book_id}.cover.medium.jpg'
                        
                        books.append({
                            'title': title,
                            'author': author,
                            'cover': cover_url,
                            'link': f'{cls.BASE_URL}/ebooks/{book_id}',
                            'source': 'gutenberg',
                            'source_id': book_id,
                            'language': 'en',
                            'can_read_online': True
                        })
                        
                    except Exception as e:
                        logger.error(f"Error processing book entry: {e}")
                        continue
                
                return books
                
        except Exception as e:
            logger.error(f"Error in GutenbergScraper search: {e}")
        return []

    @classmethod
    def get_book_content(cls, book_id):
        """Get full book content with metadata"""
        cls._delay()
        try:
            # Get book metadata
            metadata_url = f'{cls.BASE_URL}/ebooks/{book_id}'
            response = requests.get(metadata_url)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract metadata
            title = soup.select_one('h1').text.strip()
            author_elem = soup.select_one('.author')
            author = author_elem.text.strip() if author_elem else 'Unknown'
            
            # Get book content
            content_url = f'{cls.MIRROR_URL}/{book_id}/pg{book_id}.txt'
            response = requests.get(content_url)
            if response.status_code != 200:
                return None

            content = response.text
            content = cls._clean_content(content)

            # Extract summary (first few paragraphs)
            paragraphs = content.split('\n\n')
            summary = '\n\n'.join(paragraphs[:3])

            return {
                'title': title,
                'author': author,
                'content': content,
                'summary': summary,
                'cover_url': f'{cls.BASE_URL}/cache/epub/{book_id}/pg{book_id}.cover.medium.jpg',
                'source_url': metadata_url,
                'language': 'en',
                'file_type': 'txt'
            }
            
        except Exception as e:
            logger.error(f"Error fetching Gutenberg book content: {e}")
            return None

    @staticmethod
    def _clean_content(content):
        """Clean up the book content"""
        # Remove Project Gutenberg header and footer
        content = re.sub(r'^\s*The Project Gutenberg.*?\*\*\*.*?START OF.*?\*\*\*', '', content, flags=re.DOTALL)
        content = re.sub(r'\*\*\*.*?END OF.*?Project Gutenberg.*?$', '', content, flags=re.DOTALL)
        
        # Clean up whitespace
        content = re.sub(r'\r\n', '\n', content)
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content.strip()

    @classmethod
    def get_featured_books(cls, limit=5):
        """Get featured books from Project Gutenberg"""
        return cls.search_books("popular books", limit)

    @classmethod
    def get_trending_books(cls, limit=5):
        """Get trending books based on recent downloads"""
        return cls.search_books("popular downloads", limit)

    @classmethod
    def get_books_by_category(cls, category: str, limit: int = 5):
        """Get books by category"""
        return cls.search_books(f"{category} books", limit)

# Goodreads Scraper
class GoodreadsScraper:
    BASE_URL = 'https://www.goodreads.com'

    @staticmethod
    def _delay():
        time.sleep(1)  # Add 1 second delay between requests

    @classmethod
    def search_books(cls, query):
        cls._delay()  # Add delay before request
        search_url = f'{cls.BASE_URL}/search?q={query}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            response = requests.get(search_url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                books = []
                for result in soup.select('tr[itemtype="http://schema.org/Book"]'):
                    title_element = result.select_one('.bookTitle')
                    author_element = result.select_one('.authorName')
                    cover_element = result.select_one('img.bookCover')
                    if title_element and author_element and cover_element:  # Check all fields are available
                        books.append({
                            'title': title_element.text.strip(),
                            'author': author_element.text.strip(),
                            'cover': cover_element['src'],
                            'link': GoodreadsScraper.BASE_URL + title_element['href']
                        })
                return books
        except Exception as e:
            print(f"Error in GoodreadsScraper: {e}")
        return []

# Internet Archive Scraper
class InternetArchiveScraper:
    BASE_URL = 'https://archive.org'

    @staticmethod
    def _delay():
        time.sleep(1)  # Add 1 second delay between requests

    @classmethod
    def search_books(cls, query):
        cls._delay()  # Add delay before request
        search_url = f'{cls.BASE_URL}/search.php?query={query}&and[]=mediatype:texts'
        try:
            response = requests.get(search_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                books = []
                for result in soup.select('.result-item'):
                    title = result.select_one('.ttl').text.strip()
                    author = result.select_one('.creator').text.strip() if result.select_one('.creator') else 'Unknown'
                    cover = result.select_one('img')['src'] if result.select_one('img') else None
                    link = InternetArchiveScraper.BASE_URL + result.select_one('a')['href']
                    books.append({
                        'title': title,
                        'author': author,
                        'cover': cover,
                        'link': link
                    })
                return books
        except Exception as e:
            print(f"Error in InternetArchiveScraper: {e}")
        return []

    @staticmethod
    def fetch_book_content(book_id):
        book_url = f'{InternetArchiveScraper.BASE_URL}/download/{book_id}'
        try:
            response = requests.get(book_url)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"Error fetching book content from Internet Archive: {e}")
        return None

    @staticmethod
    def fetch_full_book_content(identifier):
        try:
            # Get metadata
            metadata_url = f'{InternetArchiveScraper.BASE_URL}/metadata/{identifier}'
            metadata_response = requests.get(metadata_url)
            if metadata_response.status_code == 200:
                metadata = metadata_response.json()
                
                # Try different formats
                formats = [
                    f'{InternetArchiveScraper.BASE_URL}/download/{identifier}/{identifier}_djvu.txt',
                    f'{InternetArchiveScraper.BASE_URL}/download/{identifier}/{identifier}.txt',
                    f'{InternetArchiveScraper.BASE_URL}/download/{identifier}/{identifier}_text.pdf'
                ]
                
                for format_url in formats:
                    try:
                        content_response = requests.get(format_url)
                        if content_response.status_code == 200:
                            return {
                                'content': content_response.text,
                                'title': metadata.get('metadata', {}).get('title', 'Unknown'),
                                'author': metadata.get('metadata', {}).get('creator', 'Unknown'),
                                'cover_url': f'{InternetArchiveScraper.BASE_URL}/services/img/{identifier}',
                                'source_url': f'{InternetArchiveScraper.BASE_URL}/details/{identifier}'
                            }
                    except Exception as e:
                        print(f"Error fetching format {format_url}: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error in Internet Archive full content fetch: {e}")
        return None

    @classmethod
    def get_featured_books(cls, limit: int = 5) -> List[Dict]:
        try:
            response = requests.get(f"{cls.BASE_URL}/details/texts")
            soup = BeautifulSoup(response.text, 'html.parser')
            books = []
            
            for book in soup.select('.item-ia')[:limit]:
                title = book.select_one('.title').text.strip()
                author = book.select_one('.creator').text.strip() if book.select_one('.creator') else 'Unknown'
                book_id = book['data-id']
                
                books.append({
                    'title': title,
                    'author': author,
                    'source': 'archive',
                    'source_id': book_id,
                    'cover_url': f"{cls.BASE_URL}/services/img/{book_id}",
                    'can_read_online': True
                })
            
            return books
        except Exception as e:
            print(f"Error fetching featured Internet Archive books: {e}")
            return []

    @classmethod
    def get_trending_books(cls, limit: int = 5) -> List[Dict]:
        return cls.get_featured_books(limit)

    @classmethod
    def get_books_by_category(cls, category: str, limit: int = 5) -> List[Dict]:
        return cls.get_featured_books(limit)  # Simplified for now

# Standard Ebooks Scraper
class StandardEbooksScraper:
    BASE_URL = 'https://standardebooks.org'

    @staticmethod
    def _delay():
        time.sleep(1)  # Add 1 second delay between requests

    @classmethod
    def search_books(cls, query):
        cls._delay()  # Add delay before request
        search_url = f'{cls.BASE_URL}/search?q={query}'
        try:
            response = requests.get(search_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                books = []
                for result in soup.select('.book'):
                    title = result.select_one('.title').text.strip()
                    author = result.select_one('.author').text.strip() if result.select_one('.author') else 'Unknown'
                    cover = result.select_one('img')['src'] if result.select_one('img') else None
                    link = StandardEbooksScraper.BASE_URL + result.select_one('a')['href']
                    books.append({
                        'title': title,
                        'author': author,
                        'cover': cover,
                        'link': link
                    })
                return books
        except Exception as e:
            print(f"Error in StandardEbooksScraper: {e}")
        return []

    @classmethod
    def get_featured_books(cls, limit: int = 5) -> List[Dict]:
        try:
            response = requests.get(f"{cls.BASE_URL}/ebooks/")
            soup = BeautifulSoup(response.text, 'html.parser')
            books = []
            
            for book in soup.select('.ebook')[:limit]:
                title = book.select_one('h3').text.strip()
                author = book.select_one('.author').text.strip()
                book_id = book.select_one('a')['href'].split('/')[-1]
                
                books.append({
                    'title': title,
                    'author': author,
                    'source': 'standard',
                    'source_id': book_id,
                    'cover_url': f"{cls.BASE_URL}/images/covers/{book_id}-cover.jpg",
                    'can_read_online': True
                })
            
            return books
        except Exception as e:
            print(f"Error fetching featured Standard Ebooks: {e}")
            return []

    @classmethod
    def get_trending_books(cls, limit: int = 5) -> List[Dict]:
        return cls.get_featured_books(limit)

    @classmethod
    def get_books_by_category(cls, category: str, limit: int = 5) -> List[Dict]:
        return cls.get_featured_books(limit)  # Simplified for now

# ManyBooks Scraper
class ManyBooksScraper:
    BASE_URL = 'https://manybooks.net'

    @staticmethod
    def _delay():
        time.sleep(1)  # Add 1 second delay between requests

    @classmethod
    def search_books(cls, query):
        cls._delay()  # Add delay before request
        search_url = f'{cls.BASE_URL}/search?q={query}'
        try:
            response = requests.get(search_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                books = []
                for result in soup.select('.book'):
                    title = result.select_one('.title').text.strip()
                    author = result.select_one('.author').text.strip() if result.select_one('.author') else 'Unknown'
                    cover = result.select_one('img')['src'] if result.select_one('img') else None
                    link = ManyBooksScraper.BASE_URL + result.select_one('a')['href']
                    books.append({
                        'title': title,
                        'author': author,
                        'cover': cover,
                        'link': link
                    })
                return books
        except Exception as e:
            print(f"Error in ManyBooksScraper: {e}")
        return []

# Free eBooks on Smashwords Scraper
class SmashwordsScraper:
    BASE_URL = 'https://www.smashwords.com'

    @staticmethod
    def _delay():
        time.sleep(1)  # Add 1 second delay between requests

    @classmethod
    def search_books(cls, query):
        cls._delay()  # Add delay before request
        search_url = f'{cls.BASE_URL}/books/search'
        params = {'q': query}
        try:
            response = requests.get(search_url, params=params)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                books = []
                for result in soup.select('.book'):
                    title = result.select_one('.title').text.strip()
                    author = result.select_one('.author').text.strip() if result.select_one('.author') else 'Unknown'
                    cover = result.select_one('img')['src'] if result.select_one('img') else None
                    link = SmashwordsScraper.BASE_URL + result.select_one('a')['href']
                    books.append({
                        'title': title,
                        'author': author,
                        'cover': cover,
                        'link': link
                    })
                return books
        except Exception as e:
            print(f"Error in SmashwordsScraper: {e}")
        return []

# Rate-limiting function
def rate_limit_request(func):
    def wrapper(*args, **kwargs):
        time.sleep(1)  # Sleep for 1 second between requests
        return func(*args, **kwargs)
    return wrapper

# NoteGPT Scraper
class NoteGPTScraper:
    BASE_URL = "https://notegpt.io"

    @classmethod
    def get_featured_books(cls, limit: int = 5) -> List[Dict]:
        try:
            response = requests.get(f"{cls.BASE_URL}/books")
            soup = BeautifulSoup(response.text, 'html.parser')
            books = []
            
            # Adjust the selector based on the actual HTML structure
            for book in soup.select('.book-card')[:limit]:  # Adjust selector as needed
                title = book.select_one('.book-title').text.strip()
                author = book.select_one('.book-author').text.strip()
                cover_url = book.select_one('img')['src']
                book_id = book.select_one('a')['href'].split('/')[-1]
                
                books.append({
                    'title': title,
                    'author': author,
                    'cover_url': cover_url,
                    'source': 'notegpt',
                    'source_id': book_id,
                    'can_read_online': True
                })
            
            return books
        except Exception as e:
            print(f"Error fetching NoteGPT books: {e}")
            return []

    @classmethod
    def get_trending_books(cls, limit: int = 5) -> List[Dict]:
        return cls.get_featured_books(limit)  # Use same endpoint for now

    @classmethod
    def get_books_by_category(cls, category: str, limit: int = 5) -> List[Dict]:
        try:
            # Adjust URL based on actual category endpoint
            response = requests.get(f"{cls.BASE_URL}/books/category/{category.lower()}")
            soup = BeautifulSoup(response.text, 'html.parser')
            books = []
            
            for book in soup.select('.book-card')[:limit]:
                title = book.select_one('.book-title').text.strip()
                author = book.select_one('.book-author').text.strip()
                cover_url = book.select_one('img')['src']
                book_id = book.select_one('a')['href'].split('/')[-1]
                
                books.append({
                    'title': title,
                    'author': author,
                    'cover_url': cover_url,
                    'source': 'notegpt',
                    'source_id': book_id,
                    'can_read_online': True
                })
            
            return books
        except Exception as e:
            print(f"Error fetching NoteGPT books by category: {e}")
            return []

    @classmethod
    def get_book_content(cls, book_id: str) -> Optional[Dict]:
        try:
            response = requests.get(f"{cls.BASE_URL}/books/{book_id}")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = soup.select_one('.book-title').text.strip()
            author = soup.select_one('.book-author').text.strip()
            content = soup.select_one('.book-content').text.strip()
            cover_url = soup.select_one('.book-cover img')['src']
            
            return {
                'title': title,
                'author': author,
                'content': content,
                'cover_url': cover_url,
                'source': 'notegpt',
                'source_id': book_id
            }
        except Exception as e:
            print(f"Error fetching NoteGPT book content: {e}")
            return None

# Add after other scraper classes
class AnnasArchiveScraper:
    BASE_URL = "https://annas-archive.org"
    API_URL = "https://annas-archive.org/api"

    @staticmethod
    def _delay():
        time.sleep(1)  # Add 1 second delay between requests

    @classmethod
    def search_books(cls, query, limit=10):
        cls._delay()
        try:
            # Encode query for URL
            encoded_query = quote(query)
            search_url = f"{cls.API_URL}/search/all?q={encoded_query}&limit={limit}"
            
            response = requests.get(search_url)
            if response.status_code == 200:
                data = response.json()
                books = []
                
                for item in data.get('results', []):
                    # Extract cover URL
                    cover_url = f"{cls.BASE_URL}/cover/{item.get('cover_url')}" if item.get('cover_url') else None
                    
                    books.append({
                        'title': item.get('title', 'Unknown'),
                        'author': item.get('author', 'Unknown'),
                        'cover': cover_url,
                        'link': f"{cls.BASE_URL}/md5/{item.get('md5')}",
                        'source': 'annas_archive',
                        'source_id': item.get('md5'),
                        'file_type': item.get('file_type', ''),
                        'file_size': item.get('file_size', ''),
                        'language': item.get('language', 'en'),
                        'year': item.get('year'),
                        'publisher': item.get('publisher'),
                        'can_read_online': True
                    })
                return books
        except Exception as e:
            print(f"Error in AnnasArchiveScraper search: {e}")
        return []

    @classmethod
    def get_book_content(cls, md5_hash):
        cls._delay()
        try:
            # Get book details
            detail_url = f"{cls.API_URL}/book/{md5_hash}"
            response = requests.get(detail_url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Get download link
                download_url = data.get('download_url')
                if download_url:
                    content_response = requests.get(download_url)
                    if content_response.status_code == 200:
                        return {
                            'content': content_response.content,
                            'title': data.get('title'),
                            'author': data.get('author'),
                            'cover_url': f"{cls.BASE_URL}/cover/{data.get('cover_url')}",
                            'file_type': data.get('file_type'),
                            'language': data.get('language'),
                            'year': data.get('year'),
                            'publisher': data.get('publisher')
                        }
        except Exception as e:
            print(f"Error in AnnasArchiveScraper content fetch: {e}")
        return None

    @classmethod
    def get_featured_books(cls, limit=5):
        # Get popular/featured books
        return cls.search_books("best sellers", limit)

    @classmethod
    def get_trending_books(cls, limit=5):
        # Get trending books
        return cls.search_books("trending", limit)

    @classmethod
    def get_books_by_category(cls, category: str, limit: int = 5):
        return cls.search_books(category, limit)

# Usage Example
if __name__ == "__main__":
    query = "Harry Potter"
    print("OpenLibrary Results:", OpenLibraryScraper.search_books(query))
    print("Gutenberg Results:", GutenbergScraper.search_books(query))
    print("Goodreads Results:", GoodreadsScraper.search_books(query))
    print("Internet Archive Results:", InternetArchiveScraper.search_books(query))
    print("Standard Ebooks Results:", StandardEbooksScraper.search_books(query))
    print("ManyBooks Results:", ManyBooksScraper.search_books(query))
    print("Smashwords Results:", SmashwordsScraper.search_books(query))
    
    # Fetching content (if available) for the first book from each platform
    openlibrary_books = OpenLibraryScraper.search_books(query)
    if openlibrary_books:
        book_content = OpenLibraryScraper.fetch_book_content(openlibrary_books[0]['link'].split('/')[-1])
        print("OpenLibrary Book Content:", book_content)

    gutenberg_books = GutenbergScraper.search_books(query)
    if gutenberg_books:
        book_content = GutenbergScraper.fetch_book_content(gutenberg_books[0]['link'].split('/')[-1])
        print("Gutenberg Book Content:", book_content)

    goodreads_books = GoodreadsScraper.search_books(query)
    if goodreads_books:
        print("Goodreads Book Link:", goodreads_books[0]['link'])

    internet_archive_books = InternetArchiveScraper.search_books(query)
    if internet_archive_books:
        book_content = InternetArchiveScraper.fetch_book_content(internet_archive_books[0]['link'].split('/')[-1])
        print("Internet Archive Book Content:", book_content)

    standard_ebooks_books = StandardEbooksScraper.search_books(query)
    if standard_ebooks_books:
        book_content = StandardEbooksScraper.fetch_book_content(standard_ebooks_books[0]['link'].split('/')[-1])
        print("Standard Ebooks Book Content:", book_content)

    many_books_books = ManyBooksScraper.search_books(query)
    if many_books_books:
        book_content = ManyBooksScraper.fetch_book_content(many_books_books[0]['link'].split('/')[-1])
        print("ManyBooks Book Content:", book_content)

    smashwords_books = SmashwordsScraper.search_books(query)
    if smashwords_books:
        book_content = SmashwordsScraper.fetch_book_content(smashwords_books[0]['link'].split('/')[-1])
        print("Smashwords Book Content:", book_content)
