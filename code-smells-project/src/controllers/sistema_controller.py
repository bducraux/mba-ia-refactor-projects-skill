from flask import jsonify, request

from src.utils.constants import API_VERSAO
from src.utils.errors import DatabaseUnavailableError
from src.validators.admin_validator import validar_query


class SistemaController:
    """Rotas de sistema: índice, health check, relatório e operações administrativas."""

    def __init__(self, health_service, relatorio_service, admin_service, ambiente):
        self.health = health_service
        self.relatorios = relatorio_service
        self.admin = admin_service
        self.ambiente = ambiente

    def index(self):
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": API_VERSAO,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    def health_check(self):
        try:
            counts = self.health.contagens()
        except DatabaseUnavailableError as exc:
            return jsonify({"status": "erro", "detalhes": exc.mensagem}), 500
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": counts,
            "versao": API_VERSAO,
            "ambiente": self.ambiente,
        }), 200

    def relatorio_vendas(self):
        return jsonify({"dados": self.relatorios.vendas(), "sucesso": True}), 200

    def reset_db(self):
        self.admin.resetar_banco()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    def executar_query(self):
        sql = validar_query(request.get_json(silent=True))
        return jsonify({"dados": self.admin.consultar(sql), "sucesso": True}), 200
