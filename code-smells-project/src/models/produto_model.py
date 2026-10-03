CAMPOS_PRODUTO = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _para_dict(row):
    return {campo: row[campo] for campo in CAMPOS_PRODUTO}


class ProdutoModel:
    def __init__(self, db):
        self.db = db

    def listar(self):
        rows = self.db.connection().execute("SELECT * FROM produtos").fetchall()
        return [_para_dict(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self.db.connection().execute(
            "SELECT * FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        return _para_dict(row) if row else None

    def buscar_por_ids(self, produto_ids):
        ids = list(dict.fromkeys(produto_ids))
        if not ids:
            return {}
        marcadores = ",".join("?" * len(ids))
        rows = self.db.connection().execute(
            f"SELECT * FROM produtos WHERE id IN ({marcadores})", ids
        ).fetchall()
        return {row["id"]: _para_dict(row) for row in rows}

    def pesquisar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        clausulas, params = [], []
        if termo:
            clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            clausulas.append("categoria = ?")
            params.append(categoria)
        if preco_min:
            clausulas.append("preco >= ?")
            params.append(preco_min)
        if preco_max:
            clausulas.append("preco <= ?")
            params.append(preco_max)
        sql = "SELECT * FROM produtos"
        if clausulas:
            sql += " WHERE " + " AND ".join(clausulas)
        rows = self.db.connection().execute(sql, params).fetchall()
        return [_para_dict(row) for row in rows]

    def criar(self, nome, descricao, preco, estoque, categoria):
        conn = self.db.connection()
        with conn:
            cursor = conn.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        conn = self.db.connection()
        with conn:
            conn.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def deletar(self, produto_id):
        conn = self.db.connection()
        with conn:
            conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def contar(self):
        return self.db.connection().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
