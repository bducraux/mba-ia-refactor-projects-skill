from flask import Blueprint

from src.middlewares.auth import require_admin_token


def build_sistema_routes(controller, admin_token):
    admin_only = require_admin_token(admin_token)
    bp = Blueprint("sistema", __name__)
    bp.add_url_rule("/", "index", controller.index, methods=["GET"])
    bp.add_url_rule("/health", "health_check", controller.health_check, methods=["GET"])
    bp.add_url_rule("/relatorios/vendas", "relatorio_vendas", controller.relatorio_vendas, methods=["GET"])
    bp.add_url_rule("/admin/reset-db", "reset_database", admin_only(controller.reset_db), methods=["POST"])
    bp.add_url_rule("/admin/query", "executar_query", admin_only(controller.executar_query), methods=["POST"])
    return bp
