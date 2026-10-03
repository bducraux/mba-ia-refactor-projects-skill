from src.utils.constants import (
    PRODUTO_DESCONHECIDO,
    STATUS_APROVADO,
    STATUS_CANCELADO,
    STATUS_PENDENTE,
)
from src.utils.errors import BusinessRuleError


class PedidoModel:
    def __init__(self, db):
        self.db = db

    def criar(self, usuario_id, itens, total):
        """Cria pedido, itens e baixa de estoque numa única transação.

        `itens`: [{"produto_id", "quantidade", "preco_unitario", "nome"}].
        A baixa só ocorre se ainda houver estoque; caso contrário tudo é desfeito.
        """
        conn = self.db.connection()
        with conn:
            cursor = conn.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PENDENTE, total),
            )
            pedido_id = cursor.lastrowid
            for item in itens:
                conn.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                    (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
                )
                baixa = conn.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                    (item["quantidade"], item["produto_id"], item["quantidade"]),
                )
                if baixa.rowcount == 0:
                    raise BusinessRuleError(
                        "Estoque insuficiente para " + item["nome"], payload={"sucesso": False}
                    )
        return pedido_id

    def listar(self, usuario_id=None):
        filtro, params = "", ()
        if usuario_id is not None:
            filtro, params = " WHERE usuario_id = ?", (usuario_id,)
        conn = self.db.connection()
        pedidos = conn.execute(f"SELECT * FROM pedidos{filtro} ORDER BY id", params).fetchall()
        itens = conn.execute(
            f"""
            SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario,
                   COALESCE(p.nome, ?) AS produto_nome
            FROM itens_pedido ip
            LEFT JOIN produtos p ON p.id = ip.produto_id
            WHERE ip.pedido_id IN (SELECT id FROM pedidos{filtro})
            ORDER BY ip.id
            """,
            (PRODUTO_DESCONHECIDO, *params),
        ).fetchall()

        itens_por_pedido = {}
        for item in itens:
            itens_por_pedido.setdefault(item["pedido_id"], []).append({
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"],
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
            })
        return [
            {
                "id": row["id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": itens_por_pedido.get(row["id"], []),
            }
            for row in pedidos
        ]

    def atualizar_status(self, pedido_id, novo_status):
        conn = self.db.connection()
        with conn:
            conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))

    def resumo_vendas(self):
        row = self.db.connection().execute(
            """
            SELECT COUNT(*) AS total_pedidos,
                   COALESCE(SUM(total), 0) AS faturamento,
                   COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes,
                   COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados,
                   COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados
            FROM pedidos
            """,
            (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
        ).fetchone()
        return dict(row)

    def contar(self):
        return self.db.connection().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
