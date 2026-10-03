from flask import jsonify, request

from src.validators.pedido_validator import validar_novo_pedido, validar_status


class PedidoController:
    def __init__(self, service):
        self.service = service

    def criar(self):
        dados = validar_novo_pedido(request.get_json(silent=True))
        resultado = self.service.criar(**dados)
        return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201

    def listar_todos(self):
        return jsonify({"dados": self.service.listar_todos(), "sucesso": True}), 200

    def listar_do_usuario(self, usuario_id):
        return jsonify({"dados": self.service.listar_do_usuario(usuario_id), "sucesso": True}), 200

    def atualizar_status(self, pedido_id):
        novo_status = validar_status(request.get_json(silent=True))
        self.service.atualizar_status(pedido_id, novo_status)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
