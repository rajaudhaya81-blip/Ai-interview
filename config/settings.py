import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Supabase connection
    # SQLAlchemy requires postgresql:// instead of postgres://
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Fallback to local SQLite for development if no database URL is provided
    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:///interview.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Supabase Credentials
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    
    # Gemini API Credentials
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # Local upload path (if Supabase upload fails or as a cache)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
