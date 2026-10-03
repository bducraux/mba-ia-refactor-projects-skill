from itsdangerous import BadSignature

from utils.errors import ForbiddenError, UnauthorizedError

INVALID_CREDENTIALS = 'Credenciais inválidas'


class AuthService:
    """Login and signed, expiring session tokens (itsdangerous serializer injected by the composition root)."""

    def __init__(self, user_model, serializer, token_max_age):
        self.users = user_model
        self.serializer = serializer
        self.token_max_age = token_max_age

    def login(self, email, password):
        user = self.users.find_by_email(email)
        if not user or not user.check_password(password):
            raise UnauthorizedError(INVALID_CREDENTIALS)
        if not user.active:
            raise ForbiddenError('Usuário inativo')
        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': self.serializer.dumps({'user_id': user.id}),
        }

    def resolve_user(self, token):
        """Return the active user that owns a valid token, or None."""
        if not token:
            return None
        try:
            payload = self.serializer.loads(token, max_age=self.token_max_age)
        except BadSignature:
            return None
        user = self.users.find(payload.get('user_id'))
        return user if user and user.active else None

    def require_admin(self, token):
        user = self.resolve_user(token)
        if user is None:
            raise UnauthorizedError('Token inválido ou ausente')
        if not user.is_admin():
            raise ForbiddenError('Acesso negado')
        return user
