import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': err.message}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):  # unknown routes, wrong methods, malformed JSON
            return err
        logger.exception('Unhandled error')
        return jsonify({'error': 'Erro interno'}), 500
