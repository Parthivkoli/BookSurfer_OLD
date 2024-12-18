import requests
from typing import Dict, List, Optional
from datetime import datetime
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class BookFetcher:
    """Unified service to fetch books from multiple sources"""
    
    @staticmethod
    def fetch_book_details(source: str, book_id: str) -> Optional[Dict]:
        """Fetch detailed book information from specified source"""
        try:
            fetchers = {
                'openlibrary': OpenLibraryFetcher,
                'gutenberg': GutenbergFetcher,
                'archive': InternetArchiveFetcher,
                'local': LocalBookFetcher
            }
            
            fetcher = fetchers.get(source)
            if not fetcher:
                logger.error(f"Invalid source: {source}")
                return None
                
            return fetcher.get_book_details(book_id)
            
        except Exception as e:
            logger.error(f"Error fetching book details: {e}")
            return None

    @staticmethod
    def search_books(query: str, limit: int = 10) -> List[Dict]:
        """Search books across all sources"""
        results = []
        try:
            # Search in local database first
            local_results = LocalBookFetcher.search_books(query, limit=limit//2)
            results.extend(local_results)
            
            # Search external sources
            sources = [OpenLibraryFetcher, GutenbergFetcher, InternetArchiveFetcher]
            for source in sources:
                try:
                    source_results = source.search_books(query, limit=limit//2)
                    results.extend(source_results)
                except Exception as e:
                    logger.error(f"Error searching {source.__name__}: {e}")
                    continue
                    
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error in search_books: {e}")
            return [] 