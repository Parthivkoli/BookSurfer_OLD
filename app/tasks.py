from flask_apscheduler import APScheduler
from app.utils.book_cache import BookCache

scheduler = APScheduler()

def init_scheduler(app):
    scheduler.init_app(app)
    scheduler.start()

    # Refresh cache every 24 hours
    @scheduler.task('interval', id='refresh_book_cache', hours=24)
    def refresh_book_cache():
        with app.app_context():
            BookCache.refresh_cache() 