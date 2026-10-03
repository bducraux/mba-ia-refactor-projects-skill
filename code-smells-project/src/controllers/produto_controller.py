from flask import jsonify, request

from src.utils.errors import NotFoundError
from src.validators.produto_validator import validar_filtros_busca, validar_produto


class ProdutoController:
    def __init__(self, service):
        self.service = service

    def listar(self):
        return jsonify({"dados": self.service.listar(), "sucesso": True}), 200

    def buscar(self):
        resultados = self.service.pesquisar(validar_filtros_busca(request.args))
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    def obter(self, produto_id):
        produto = self.service.buscar_por_id(produto_id)
        if produto is None:
            raise NotFoundError("Produto não encontrado", payload={"sucesso": False})
        return jsonify({"dados": produto, "sucesso": True}), 200

    def criar(self):
        dados = validar_produto(request.get_json(silent=True))
        produto_id = self.service.criar(dados)
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    def atualizar(self, produto_id):
        self.service.garantir_existe(produto_id)
        dados = validar_produto(request.get_json(silent=True), regras_de_cadastro=False)
        self.service.atualizar(produto_id, dados)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, produto_id):
        self.service.deletar(produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
