import logging
import sqlite3

from src.utils.errors import DatabaseUnavailableError

logger = logging.getLogger(__name__)


class HealthService:
    def __init__(self, produtos, usuarios, pedidos):
        self.produtos = produtos
        self.usuarios = usuarios
        self.pedidos = pedidos

    def contagens(self):
        try:
            return {
                "produtos": self.produtos.contar(),
                "usuarios": self.usuarios.contar(),
                "pedidos": self.pedidos.contar(),
            }
        except sqlite3.Error as exc:
            logger.exception("Health check falhou")
            raise DatabaseUnavailableError("Banco de dados indisponível") from exc
