from flask import Flask, jsonify, request
from app.utils.scraper import OpenLibraryScraper, GutenbergScraper

app = Flask(__name__)

@app.route('/api/search_books', methods=['GET'])
def search_books_api():
    query = request.args.get('query', '')
    title = request.args.get('title', '')
    author = request.args.get('author', '')

    # Combine query parameters
    combined_query = ' '.join(filter(None, [query, title, author]))

    # Fetch books from OpenLibrary
    openlibrary_results = OpenLibraryScraper.search_books(combined_query)

    # Fetch books from Gutenberg
    gutenberg_results = GutenbergScraper.search_books(combined_query)

    # Combine results
    results = {
        'openlibrary': openlibrary_results,
        'gutenberg': gutenberg_results
    }

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)