from flask import Blueprint
from app.models.book import Book
from app.models.bookmark import Bookmark
from app.extensions import db

# Import blueprints from route modules
from .main import main_bp
from .auth import auth_bp
from .books import books_bp
from .api import api_bp

# Export blueprints
__all__ = ['main_bp', 'auth_bp', 'books_bp', 'api_bp']
