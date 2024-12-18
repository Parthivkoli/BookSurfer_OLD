import requests
from typing import List, Dict, Optional

class GoogleBooksAPI:
    BASE_URL = "https://www.googleapis.com/books/v1"
    API_KEY = "AIzaSyD3RqDH_icgyfP0lAds58VVBQ_6frPx4-s"

    @classmethod
    def search_books(cls, query: str, max_results: int = 10) -> List[Dict]:
        try:
            url = f"{cls.BASE_URL}/volumes"
            params = {
                'q': query,
                'maxResults': max_results,
                'key': cls.API_KEY
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            books = []
            for item in data.get('items', []):
                volume_info = item.get('volumeInfo', {})
                books.append({
                    'title': volume_info.get('title', 'Unknown'),
                    'author': ', '.join(volume_info.get('authors', ['Unknown'])),
                    'cover_url': volume_info.get('imageLinks', {}).get('thumbnail'),
                    'description': volume_info.get('description', ''),
                    'source': 'google',
                    'source_id': item.get('id'),
                    'preview_link': volume_info.get('previewLink'),
                    'categories': volume_info.get('categories', []),
                    'published_date': volume_info.get('publishedDate'),
                    'is_public_domain': False,  # Google Books API doesn't easily expose this
                    'can_read_online': False
                })
            return books
        except Exception as e:
            print(f"Error fetching books from Google Books API: {e}")
            return []

    @classmethod
    def get_book_by_id(cls, book_id: str) -> Optional[Dict]:
        try:
            url = f"{cls.BASE_URL}/volumes/{book_id}"
            params = {'key': cls.API_KEY}
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            volume_info = data.get('volumeInfo', {})
            return {
                'title': volume_info.get('title', 'Unknown'),
                'author': ', '.join(volume_info.get('authors', ['Unknown'])),
                'cover_url': volume_info.get('imageLinks', {}).get('thumbnail'),
                'description': volume_info.get('description', ''),
                'preview_link': volume_info.get('previewLink'),
                'categories': volume_info.get('categories', []),
                'published_date': volume_info.get('publishedDate'),
                'is_public_domain': False,
                'can_read_online': False
            }
        except Exception as e:
            print(f"Error fetching book details from Google Books API: {e}")
            return None 