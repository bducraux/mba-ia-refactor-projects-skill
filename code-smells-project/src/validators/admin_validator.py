from src.utils.errors import ValidationError


def validar_query(dados):
    query = dados.get("sql", "") if isinstance(dados, dict) else ""
    if not query or not isinstance(query, str):
        raise ValidationError("Query não informada")
    if not query.strip().upper().startswith("SELECT"):
        raise ValidationError("Apenas consultas SELECT são permitidas")
    return query
