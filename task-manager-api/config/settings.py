import os

from dotenv import load_dotenv

load_dotenv()

DEV_SECRET_KEY = 'dev-only-change-me'


def _bool(name, default):
    return os.environ.get(name, default).strip().lower() in ('1', 'true', 'yes', 'on')


class Settings:
    SECRET_KEY = os.environ.get('SECRET_KEY', DEV_SECRET_KEY)
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    DEBUG = _bool('FLASK_DEBUG', 'false')
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', '5000'))
    CORS_ORIGINS = [o.strip() for o in os.environ.get('CORS_ORIGINS', '*').split(',') if o.strip()]
    TOKEN_MAX_AGE_SECONDS = int(os.environ.get('TOKEN_MAX_AGE_SECONDS', '86400'))
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    SMTP_HOST = os.environ.get('SMTP_HOST', '')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    SMTP_SENDER = os.environ.get('SMTP_SENDER', '')


settings = Settings()
