import requests

# OpenLibrary API Client
class OpenLibraryAPI:
    BASE_URL = 'https://openlibrary.org'

    @staticmethod
    def search_books(query):
        try:
            response = requests.get(f'{OpenLibraryAPI.BASE_URL}/search.json?q={query}')
            if response.status_code == 200:
                return response.json().get('docs', [])
            print(f"OpenLibraryAPI Error: Status Code {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"OpenLibraryAPI Exception: {e}")
        return []

# Internet Archive API Client
class InternetArchiveAPI:
    BASE_URL = 'https://archive.org'

    @staticmethod
    def search_books(query):
        try:
            response = requests.get(f'{InternetArchiveAPI.BASE_URL}/search.php?q={query}&output=json')
            if response.status_code == 200:
                return response.json().get('response', {}).get('docs', [])
            print(f"InternetArchiveAPI Error: Status Code {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"InternetArchiveAPI Exception: {e}")
        return []
