from utils.errors import ValidationError


def require_object(data, allow_empty=False):
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise ValidationError('Dados inválidos')
    return data


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def optional_id(value, field):
    """Accept a missing/empty reference or an integer id."""
    if value in (None, '', 0):
        return value
    if not is_int(value):
        raise ValidationError(f'{field} inválido')
    return value


def parse_int_param(raw, name):
    if raw in (None, ''):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise ValidationError(f'Parâmetro {name} inválido')
