import os
import secrets


def _bool(nome, padrao):
    return os.environ.get(nome, padrao).strip().lower() in ("1", "true", "yes", "on")


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _bool("FLASK_DEBUG", "false")
    APP_ENV = os.environ.get("APP_ENV", "producao")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))
    # Vazio = rotas /admin/* desabilitadas (sempre 403).
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")


settings = Settings()
