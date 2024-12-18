document.addEventListener('DOMContentLoaded', function () {
    // Initialize dark mode toggle
    initializeDarkModeToggle();

    // Initialize book reader controls
    if (document.getElementById('bookReaderContainer')) {
        const reader = new BookReader('bookReaderContainer');
        reader.loadBook(document.getElementById('bookReaderContainer').dataset.bookId);
        
        document.getElementById('prevPage').addEventListener('click', () => reader.prevPage());
        document.getElementById('nextPage').addEventListener('click', () => reader.nextPage());
        document.getElementById('zoomIn').addEventListener('click', () => reader.zoomIn());
        document.getElementById('zoomOut').addEventListener('click', () => reader.zoomOut());
        document.getElementById('addBookmark').addEventListener('click', () => addBookmark(reader.currentPage));
    }

    // Initialize search form with debounce
    initializeSearchForm();

    // Initialize dynamic search
    initializeDynamicSearch();
});

/**
 * Function to update dark mode preference on the server
 * @param {boolean} isDarkMode - The current dark mode state
 * @returns {Promise} - Resolves with the server response
 */
function updateDarkModePreference(isDarkMode) {
    return fetch('/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ dark_mode: isDarkMode }),
    })
        .then((response) => response.json())
        .catch((error) => {
            console.error('Error updating dark mode preference:', error);
            throw error;
        });
}

/**
 * Initialize the dark mode toggle functionality
 */
function initializeDarkModeToggle() {
    const darkModeToggle = document.getElementById('darkModeToggle');

    if (darkModeToggle) {
        darkModeToggle.addEventListener('change', function () {
            updateDarkModePreference(this.checked)
                .then((data) => {
                    if (data.status === 'success') {
                        document.body.classList.toggle('dark-mode');
                    }
                })
                .catch((error) => {
                    console.error('Error updating dark mode:', error);
                });
        });
    }
}

/**
 * Book Reader Class - Handles book navigation, zooming, bookmarking, and progress updates
 */
class BookReader {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentPage = 0;
        this.pages = [];
        this.bookId = null;
    }

    loadBook(bookId) {
        this.bookId = bookId;
        fetch(`/book/read/${bookId}`)
            .then(response => response.json())
            .then(data => {
                this.pages = data.content;
                this.totalPages = this.pages.length;
                this.loadPage(0);
            })
            .catch(error => console.error('Error loading book:', error));
    }

    loadPage(page) {
        if (page >= 0 && page < this.pages.length) {
            this.container.innerHTML = this.pages[page];
            this.currentPage = page;
            this.updateProgressBar();
        }
    }

    prevPage() {
        if (this.currentPage > 0) {
            this.loadPage(this.currentPage - 1);
        }
    }

    nextPage() {
        if (this.currentPage < this.totalPages - 1) {
            this.loadPage(this.currentPage + 1);
        }
    }

    updateProgressBar() {
        const progressBar = document.getElementById('readingProgress');
        const progress = ((this.currentPage + 1) / this.totalPages) * 100;
        progressBar.style.width = `${progress}%`;
        document.getElementById('pageNumber').value = this.currentPage + 1;
    }

    zoomIn() {
        this.container.style.zoom = '110%';
    }

    zoomOut() {
        this.container.style.zoom = '90%';
    }
}

/**
 * Initialize the search form with debounce functionality
 */
function initializeSearchForm() {
    const searchForm = document.getElementById('searchForm');

    if (searchForm) {
        let timeout;
        const debounceSearch = function () {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                const searchQuery = document.getElementById('searchQuery').value;
                const category = document.getElementById('categoryFilter').value;

                fetch(`/discover?search=${searchQuery}&category=${category}`)
                    .then((response) => response.text())
                    .then((html) => {
                        document.getElementById('bookResults').innerHTML = html;
                    })
                    .catch((error) => {
                        console.error('Error fetching search results:', error);
                    });
            }, 500); // Adjust delay as needed (500ms for debounce)
        };

        searchForm.addEventListener('input', debounceSearch); // Trigger on input change
    }
}

/**
 * Initialize dynamic search functionality
 */
function initializeDynamicSearch() {
    const searchInput = document.querySelector('input[name="query"]');
    const resultsContainer = document.getElementById('searchResults');

    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const query = searchInput.value.trim();
            if (query.length > 2) { // Perform search if query length is greater than 2
                fetch(`/api/search_books?query=${query}`)
                    .then(response => response.json())
                    .then(data => {
                        displaySearchResults(data, resultsContainer);
                    })
                    .catch(error => {
                        console.error('Error fetching search results:', error);
                    });
            }
        });
    }
}

/**
 * Display search results dynamically
 * @param {Object} data - The search results data
 * @param {HTMLElement} container - The container to display results
 */
function displaySearchResults(data, container) {
    container.innerHTML = '';
    ['openlibrary', 'gutenberg'].forEach(source => {
        const books = data[source] || [];
        books.forEach(book => {
            const bookCard = document.createElement('div');
            bookCard.classList.add('col-md-4', 'mb-4');
            const coverImage = book.cover ? book.cover : 'default-cover.jpg'; // Ensure a default cover
            bookCard.innerHTML = `
                <div class="card book-card h-100">
                    <img src="${coverImage}" class="card-img-top book-cover" alt="${book.title}">
                    <div class="card-body">
                        <h5 class="card-title">${book.title}</h5>
                        <p class="card-text"><small class="text-muted">By ${book.author}</small></p>
                    </div>
                    <div class="card-footer bg-transparent">
                        <a href="/read/${book.id}" class="btn btn-primary btn-sm">Read Now</a>
                    </div>
                </div>`;
            container.appendChild(bookCard);
        });
    });
}

function addBookmark(page) {
    fetch(`/api/books/${document.getElementById('bookReaderContainer').dataset.bookId}/bookmark`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            page_number: page,
        }),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.status === 'success') {
                alert('Bookmark added!');
            }
        })
        .catch((error) => console.error('Error adding bookmark:', error));
}
