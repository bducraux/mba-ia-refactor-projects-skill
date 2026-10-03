from flask import jsonify, request

from src.utils.errors import NotFoundError
from src.validators.usuario_validator import validar_login, validar_novo_usuario


class UsuarioController:
    def __init__(self, service):
        self.service = service

    def listar(self):
        return jsonify({"dados": self.service.listar(), "sucesso": True}), 200

    def obter(self, usuario_id):
        usuario = self.service.buscar_por_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")
        return jsonify({"dados": usuario, "sucesso": True}), 200

    def criar(self):
        dados = validar_novo_usuario(request.get_json(silent=True))
        usuario_id = self.service.criar(**dados)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login(self):
        credenciais = validar_login(request.get_json(silent=True))
        usuario = self.service.autenticar(**credenciais)
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
