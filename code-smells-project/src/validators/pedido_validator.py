from src.utils.constants import STATUS_PEDIDO_VALIDOS
from src.utils.errors import ValidationError


def _inteiro_positivo(valor):
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor if valor > 0 else None
    if isinstance(valor, str) and valor.isdigit():
        return int(valor) or None
    return None


def validar_novo_pedido(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    usuario_id = _inteiro_positivo(usuario_id)
    if usuario_id is None:
        raise ValidationError("Usuario ID inválido")
    if not itens or not isinstance(itens, list):
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    itens_validos = []
    for item in itens:
        produto_id = _inteiro_positivo(item.get("produto_id")) if isinstance(item, dict) else None
        quantidade = _inteiro_positivo(item.get("quantidade")) if isinstance(item, dict) else None
        if produto_id is None or quantidade is None:
            raise ValidationError("Item inválido: produto_id e quantidade devem ser inteiros positivos")
        itens_validos.append({"produto_id": produto_id, "quantidade": quantidade})

    return {"usuario_id": usuario_id, "itens": itens_validos}


def validar_status(dados):
    novo_status = dados.get("status", "") if isinstance(dados, dict) else ""
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise ValidationError("Status inválido")
    return novo_status
