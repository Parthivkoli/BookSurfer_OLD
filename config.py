import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder for EPUB files
    UPLOAD_FOLDER = os.path.join(basedir, 'epub')
    
    # Maximum file size for uploads (5MB)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'epub', 'pdf', 'txt'}