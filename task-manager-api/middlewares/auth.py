from functools import wraps

from flask import request

BEARER_PREFIX = 'Bearer '


def bearer_token():
    header = request.headers.get('Authorization', '')
    return header[len(BEARER_PREFIX):].strip() if header.startswith(BEARER_PREFIX) else None


def build_require_admin(auth_service):
    """Decorator factory: the wrapped view runs only for a valid token of an active admin."""

    def require_admin(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            auth_service.require_admin(bearer_token())
            return view(*args, **kwargs)

        return wrapper

    return require_admin
