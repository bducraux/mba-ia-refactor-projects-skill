import sqlite3

from src.utils.errors import ValidationError

_TABELAS_RESET = ("itens_pedido", "pedidos", "produtos", "usuarios")


class AdminModel:
    def __init__(self, db):
        self.db = db

    def resetar_dados(self):
        conn = self.db.connection()
        with conn:
            for tabela in _TABELAS_RESET:
                conn.execute(f"DELETE FROM {tabela}")

    def consultar_somente_leitura(self, sql):
        """Executa uma única instrução com o banco em modo somente leitura."""
        conn = self.db.connection()
        conn.execute("PRAGMA query_only = ON")
        try:
            rows = conn.execute(sql).fetchall()
        except sqlite3.Error as exc:
            raise ValidationError("Query inválida") from exc
        finally:
            conn.execute("PRAGMA query_only = OFF")
        return [dict(row) for row in rows]
