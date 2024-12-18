import click
from flask.cli import with_appcontext
from app.utils.book_cache import BookCache

@click.command('refresh-books')
@with_appcontext
def refresh_books_command():
    """Refresh the book cache"""
    click.echo('Refreshing book cache...')
    BookCache.refresh_cache()
    click.echo('Book cache refreshed!')

def init_app(app):
    app.cli.add_command(refresh_books_command) 