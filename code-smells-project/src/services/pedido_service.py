from src.utils.errors import BusinessRuleError


class PedidoService:
    def __init__(self, pedidos, produtos, notificacoes):
        self.pedidos = pedidos
        self.produtos = produtos
        self.notificacoes = notificacoes

    def criar(self, usuario_id, itens):
        produtos = self.produtos.buscar_por_ids([item["produto_id"] for item in itens])

        total = 0
        itens_precificados = []
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise BusinessRuleError(
                    "Produto " + str(item["produto_id"]) + " não encontrado", payload={"sucesso": False}
                )
            if produto["estoque"] < item["quantidade"]:
                raise BusinessRuleError(
                    "Estoque insuficiente para " + produto["nome"], payload={"sucesso": False}
                )
            total = total + (produto["preco"] * item["quantidade"])
            itens_precificados.append({**item, "preco_unitario": produto["preco"], "nome": produto["nome"]})

        pedido_id = self.pedidos.criar(usuario_id, itens_precificados, total)
        self.notificacoes.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar_todos(self):
        return self.pedidos.listar()

    def listar_do_usuario(self, usuario_id):
        return self.pedidos.listar(usuario_id=usuario_id)

    def atualizar_status(self, pedido_id, novo_status):
        self.pedidos.atualizar_status(pedido_id, novo_status)
        self.notificacoes.status_alterado(pedido_id, novo_status)
