import logging

from utils.errors import ForbiddenError, UnauthorizedError

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, users, token_signer):
        self.users = users
        self.token_signer = token_signer

    def login(self, email, password):
        user = self.users.get_by_email(email)
        if not user or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')
        if user.has_legacy_password_hash():
            user.set_password(password)
            user.save()
            logger.info('Upgraded legacy password hash: user id=%s', user.id)
        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': self.token_signer.sign(user.id),
        }

    def authenticate(self, token):
        if not token:
            raise UnauthorizedError('Token de autenticação ausente')
        user_id = self.token_signer.read(token)
        user = self.users.get(user_id) if user_id is not None else None
        if not user or not user.active:
            raise UnauthorizedError('Token inválido ou expirado')
        return user
