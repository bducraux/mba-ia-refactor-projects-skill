import logging

from src.utils.errors import NotFoundError

logger = logging.getLogger(__name__)


class ProdutoService:
    def __init__(self, produtos):
        self.produtos = produtos

    def listar(self):
        return self.produtos.listar()

    def pesquisar(self, filtros):
        return self.produtos.pesquisar(**filtros)

    def buscar_por_id(self, produto_id):
        return self.produtos.buscar_por_id(produto_id)

    def garantir_existe(self, produto_id):
        if self.produtos.buscar_por_id(produto_id) is None:
            raise NotFoundError("Produto não encontrado")

    def criar(self, dados):
        produto_id = self.produtos.criar(**dados)
        logger.info("Produto criado id=%s", produto_id)
        return produto_id

    def atualizar(self, produto_id, dados):
        self.produtos.atualizar(produto_id, **dados)

    def deletar(self, produto_id):
        self.garantir_existe(produto_id)
        self.produtos.deletar(produto_id)
        logger.info("Produto deletado id=%s", produto_id)
