import logging

from src.utils.errors import UnauthorizedError
from src.utils.security import hash_senha, verificar_senha

logger = logging.getLogger(__name__)


class UsuarioService:
    def __init__(self, usuarios):
        self.usuarios = usuarios

    def listar(self):
        return self.usuarios.listar()

    def buscar_por_id(self, usuario_id):
        return self.usuarios.buscar_por_id(usuario_id)

    def criar(self, nome, email, senha):
        usuario_id = self.usuarios.criar(nome, email, hash_senha(senha))
        logger.info("Usuário criado id=%s", usuario_id)
        return usuario_id

    def autenticar(self, email, senha):
        for usuario, senha_hash in self.usuarios.buscar_credenciais_por_email(email):
            if senha_hash and verificar_senha(senha_hash, senha):
                logger.info("Login bem-sucedido usuario_id=%s", usuario["id"])
                return usuario
        logger.info("Falha de login")
        raise UnauthorizedError("Email ou senha inválidos", payload={"sucesso": False})
