from werkzeug.security import check_password_hash, generate_password_hash

_PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


def hash_senha(senha):
    return generate_password_hash(senha)


def verificar_senha(senha_hash, senha):
    return check_password_hash(senha_hash, senha)


def eh_hash_de_senha(valor):
    return isinstance(valor, str) and valor.startswith(_PREFIXOS_HASH)
