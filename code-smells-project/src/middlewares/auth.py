import hmac
from functools import wraps

from flask import request

from src.utils.errors import ForbiddenError

ADMIN_TOKEN_HEADER = "X-Admin-Token"


def require_admin_token(admin_token):
    """Protege a view com o token de admin da config; sem token configurado a rota fica desabilitada."""

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            enviado = request.headers.get(ADMIN_TOKEN_HEADER, "")
            if not admin_token or not hmac.compare_digest(enviado.encode(), admin_token.encode()):
                raise ForbiddenError("Acesso negado")
            return view(*args, **kwargs)

        return wrapper

    return decorator
