class AppError(Exception):
    """Erro de domínio convertido em resposta JSON pelo error handler.

    `payload` permite manter chaves extras do envelope original (ex.: {"sucesso": False}).
    """

    status = 500

    def __init__(self, mensagem, status=None, payload=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status or self.status
        self.payload = payload or {}


class ValidationError(AppError):
    status = 400


class BusinessRuleError(AppError):
    status = 400


class UnauthorizedError(AppError):
    status = 401


class ForbiddenError(AppError):
    status = 403


class NotFoundError(AppError):
    status = 404


class DatabaseUnavailableError(AppError):
    status = 500
