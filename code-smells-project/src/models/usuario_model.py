from src.utils.constants import TIPO_USUARIO_PADRAO

# A senha (hash) nunca sai do model nas consultas públicas.
CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")
CAMPOS_LOGIN = ("id", "nome", "email", "tipo")


def _para_dict(row, campos=CAMPOS_PUBLICOS):
    return {campo: row[campo] for campo in campos}


class UsuarioModel:
    def __init__(self, db):
        self.db = db

    def listar(self):
        rows = self.db.connection().execute("SELECT * FROM usuarios").fetchall()
        return [_para_dict(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self.db.connection().execute(
            "SELECT * FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return _para_dict(row) if row else None

    def buscar_credenciais_por_email(self, email):
        """Retorna [(dados_de_login, senha_hash), ...] para o email informado."""
        rows = self.db.connection().execute(
            "SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)
        ).fetchall()
        return [(_para_dict(row, CAMPOS_LOGIN), row["senha"]) for row in rows]

    def criar(self, nome, email, senha_hash, tipo=TIPO_USUARIO_PADRAO):
        conn = self.db.connection()
        with conn:
            cursor = conn.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, tipo),
            )
        return cursor.lastrowid

    def contar(self):
        return self.db.connection().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
