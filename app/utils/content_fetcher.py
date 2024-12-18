import requests
from bs4 import BeautifulSoup
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class BookContentFetcher:
    @staticmethod
    def fetch_content(book_data: dict) -> Optional[str]:
        """Fetch book content based on source"""
        try:
            if book_data['source'] == 'gutenberg':
                return GutenbergContentFetcher.fetch_content(book_data['source_id'])
            elif book_data['source'] == 'archive':
                return ArchiveContentFetcher.fetch_content(book_data['source_id'])
            elif book_data['source'] == 'standard':
                return StandardEbooksContentFetcher.fetch_content(book_data['source_id'])
            else:
                logger.error(f"Unsupported source: {book_data['source']}")
                return None
        except Exception as e:
            logger.error(f"Error fetching content: {e}")
            return None

class GutenbergContentFetcher:
    @staticmethod
    def fetch_content(book_id: str) -> Optional[str]:
        try:
            # Try different URL patterns
            urls = [
                f"https://www.gutenberg.org/files/{book_id}/{book_id}-h/{book_id}-h.htm",
                f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}-images.html",
                f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.html"
            ]
            
            for url in urls:
                response = requests.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Remove navigation and header elements
                    for nav in soup.find_all(['nav', 'header']):
                        nav.decompose()
                    # Get main content
                    content = soup.find('body') or soup
                    return content.get_text()
            
            return None
        except Exception as e:
            logger.error(f"Error fetching Gutenberg content: {e}")
            return None
  