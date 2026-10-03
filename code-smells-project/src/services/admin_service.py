import logging

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, admin):
        self.admin = admin

    def resetar_banco(self):
        self.admin.resetar_dados()
        logger.warning("Banco de dados resetado via /admin/reset-db")

    def consultar(self, sql):
        logger.warning("Consulta administrativa executada via /admin/query")
        return self.admin.consultar_somente_leitura(sql)
