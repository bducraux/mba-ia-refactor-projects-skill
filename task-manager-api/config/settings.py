import os

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name, default):
    return os.environ.get(name, default).strip().lower() in ('1', 'true', 'yes', 'on')


class Settings:
    """Application settings read from environment variables (safe development defaults)."""

    def __init__(self):
        self.SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-me')
        self.DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
        self.DEBUG = _env_bool('FLASK_DEBUG', 'false')
        self.HOST = os.environ.get('HOST', '0.0.0.0')
        self.PORT = int(os.environ.get('PORT', '5000'))
        self.CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
        self.LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
        self.TOKEN_MAX_AGE_SECONDS = int(os.environ.get('TOKEN_MAX_AGE_SECONDS', '86400'))

        self.SMTP_HOST = os.environ.get('SMTP_HOST', '')
        self.SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
        self.SMTP_USER = os.environ.get('SMTP_USER', '')
        self.SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
        self.SMTP_SENDER = os.environ.get('SMTP_SENDER', self.SMTP_USER)
