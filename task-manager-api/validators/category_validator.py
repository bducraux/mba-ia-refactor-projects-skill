from utils.constants import DEFAULT_COLOR
from utils.errors import ValidationError
from utils.helpers import is_valid_color

INVALID_PAYLOAD = 'Dados inválidos'


def _require_payload(data):
    if not data or not isinstance(data, dict):
        raise ValidationError(INVALID_PAYLOAD)


def _check_name(name):
    if not name or not isinstance(name, str):
        raise ValidationError('Nome é obrigatório')
    return name


def _check_color(color):
    if not is_valid_color(color):
        raise ValidationError('Cor inválida')
    return color


def validate_category_create(data):
    _require_payload(data)
    return {
        'name': _check_name(data.get('name')),
        'description': data.get('description', ''),
        'color': _check_color(data.get('color', DEFAULT_COLOR)),
    }


def validate_category_update(data):
    _require_payload(data)
    changes = {}
    if 'name' in data:
        changes['name'] = _check_name(data['name'])
    if 'description' in data:
        changes['description'] = data['description']
    if 'color' in data:
        changes['color'] = _check_color(data['color'])
    return changes
