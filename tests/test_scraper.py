from app.utils.scraper import OpenLibraryScraper, GutenbergScraper, InternetArchiveScraper

def test_scrapers():
    # Test OpenLibrary
    print("\nTesting OpenLibrary Scraper...")
    query = "Pride and Prejudice"
    books = OpenLibraryScraper.search_books(query)
    if books:
        print(f"Found {len(books)} books")
        book = books[0]
        print(f"Testing book: {book['title']} by {book['author']}")
        book_id = book['link'].split('/')[-1]
        content = OpenLibraryScraper.fetch_full_book_content(book_id)
        if content:
            print("✓ Successfully fetched book content")
            print(f"Title: {content['title']}")
            print(f"Author: {content['author']}")
            print(f"Content preview: {content['content'][:200]}...")
        else:
            print("✗ Failed to fetch book content")
    else:
        print("✗ No books found")

    # Test Gutenberg
    print("\nTesting Gutenberg Scraper...")
    books = GutenbergScraper.search_books(query)
    if books:
        print(f"Found {len(books)} books")
        book = books[0]
        print(f"Testing book: {book['title']} by {book['author']}")
        book_id = book['link'].split('/')[-1].replace('ebooks/', '')
        content = GutenbergScraper.fetch_full_book_content(book_id)
        if content:
            print("✓ Successfully fetched book content")
            print(f"Title: {content['title']}")
            print(f"Author: {content['author']}")
            print(f"Content preview: {content['content'][:200]}...")
        else:
            print("✗ Failed to fetch book content")
    else:
        print("✗ No books found")

    # Test Internet Archive
    print("\nTesting Internet Archive Scraper...")
    books = InternetArchiveScraper.search_books(query)
    if books:
        print(f"Found {len(books)} books")
        book = books[0]
        print(f"Testing book: {book['title']} by {book['author']}")
        book_id = book['link'].split('/')[-1]
        content = InternetArchiveScraper.fetch_full_book_content(book_id)
        if content:
            print("✓ Successfully fetched book content")
            print(f"Title: {content['title']}")
            print(f"Author: {content['author']}")
            print(f"Content preview: {content['content'][:200]}...")
        else:
            print("✗ Failed to fetch book content")
    else:
        print("✗ No books found")

if __name__ == "__main__":
    test_scrapers() 