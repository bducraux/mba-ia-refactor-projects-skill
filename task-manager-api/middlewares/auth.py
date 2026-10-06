from functools import wraps
from types import SimpleNamespace

from flask import g, request

from utils.errors import ForbiddenError


def _bearer_token():
    scheme, _, token = request.headers.get('Authorization', '').partition(' ')
    return token.strip() if scheme.lower() == 'bearer' else None


def build_auth_guards(auth_service):
    """Route decorators: require_auth (any active user) and require_admin."""

    def require_auth(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            g.current_user = auth_service.authenticate(_bearer_token())
            return view(*args, **kwargs)
        return wrapper

    def require_admin(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = auth_service.authenticate(_bearer_token())
            if not user.is_admin():
                raise ForbiddenError('Acesso restrito a administradores')
            g.current_user = user
            return view(*args, **kwargs)
        return wrapper

    return SimpleNamespace(require_auth=require_auth, require_admin=require_admin)
