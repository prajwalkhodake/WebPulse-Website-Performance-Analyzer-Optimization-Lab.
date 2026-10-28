import os
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent

# Load environment variables from .env file if present
load_dotenv(basedir / '.env')


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'webpulse-dev-secret-key-change-in-prod-xyz987')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL:
        # Normalize plain mysql:// to mysql+pymysql:// driver
        if DATABASE_URL.startswith('mysql://'):
            DATABASE_URL = DATABASE_URL.replace('mysql://', 'mysql+pymysql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Default to an instance-located SQLite database
        instance_dir = basedir / 'instance'
        instance_dir.mkdir(exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{instance_dir / 'webpulse.sqlite3'}"

    # File Upload & Storage Limits (50 MB max archive size)
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))
    
    # Private storage directory outside public static
    STORAGE_DIR = Path(os.getenv('STORAGE_DIR', basedir / 'storage')).resolve()
    UPLOAD_FOLDER = STORAGE_DIR / 'uploads'
    EXTRACTED_FOLDER = STORAGE_DIR / 'extracted'

    # Security & Sessions
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False

    @classmethod
    def init_app(cls, app):
        """Ensure necessary storage directories exist at startup."""
        cls.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.EXTRACTED_FOLDER.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    """Configuration for local development."""
    DEBUG = True


class TestingConfig(Config):
    """Configuration for automated test execution."""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'testing-key-for-webpulse-unit-tests'
    STORAGE_DIR = basedir / 'tests' / 'test_storage'
    UPLOAD_FOLDER = STORAGE_DIR / 'uploads'
    EXTRACTED_FOLDER = STORAGE_DIR / 'extracted'


class ProductionConfig(Config):
    """Configuration for production deployment."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
