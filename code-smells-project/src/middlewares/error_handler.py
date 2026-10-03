import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.utils.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.mensagem, **err.payload}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            return err  # 404/405 de rota inexistente mantêm o comportamento padrão do Flask
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
