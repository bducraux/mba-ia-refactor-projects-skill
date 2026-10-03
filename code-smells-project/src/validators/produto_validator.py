from src.utils.constants import (
    CATEGORIA_PADRAO,
    CATEGORIAS_VALIDAS,
    NOME_PRODUTO_MAX,
    NOME_PRODUTO_MIN,
)
from src.utils.errors import ValidationError

_OBRIGATORIOS = (("nome", "Nome é obrigatório"), ("preco", "Preço é obrigatório"), ("estoque", "Estoque é obrigatório"))


def _eh_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def validar_produto(dados, *, regras_de_cadastro=True):
    """Valida o payload de produto e devolve os campos normalizados.

    `regras_de_cadastro` aplica as regras extras (tamanho do nome e categoria) que a API
    original exige apenas no POST /produtos; o PUT mantém o conjunto de regras original.
    """
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    for campo, mensagem in _OBRIGATORIOS:
        if campo not in dados:
            raise ValidationError(mensagem)

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome inválido")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição inválida")
    if not isinstance(categoria, str):
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))
    if not _eh_numero(preco):
        raise ValidationError("Preço inválido")
    if not _eh_numero(estoque):
        raise ValidationError("Estoque inválido")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")

    if regras_de_cadastro:
        if len(nome) < NOME_PRODUTO_MIN:
            raise ValidationError("Nome muito curto")
        if len(nome) > NOME_PRODUTO_MAX:
            raise ValidationError("Nome muito longo")
        if categoria not in CATEGORIAS_VALIDAS:
            raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def validar_filtros_busca(args):
    filtros = {
        "termo": args.get("q", ""),
        "categoria": args.get("categoria"),
        "preco_min": args.get("preco_min"),
        "preco_max": args.get("preco_max"),
    }
    for campo in ("preco_min", "preco_max"):
        if filtros[campo]:
            try:
                filtros[campo] = float(filtros[campo])
            except ValueError:
                raise ValidationError(f"Parâmetro {campo} inválido") from None
    return filtros
