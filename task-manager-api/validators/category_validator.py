import re

from utils.constants import COLOR_PATTERN, DEFAULT_COLOR
from utils.errors import ValidationError
from validators.common import require_object

_COLOR_RE = re.compile(COLOR_PATTERN)


def _check_color(color):
    if not isinstance(color, str) or not _COLOR_RE.match(color):
        raise ValidationError('Cor inválida')
    return color


def _check_name(name):
    if not name or not isinstance(name, str):
        raise ValidationError('Nome é obrigatório')
    return name


def validate_category_create(data):
    require_object(data)
    return {
        'name': _check_name(data.get('name')),
        'description': data.get('description', ''),
        'color': _check_color(data.get('color', DEFAULT_COLOR)),
    }


def validate_category_update(data):
    require_object(data, allow_empty=True)
    changes = {}
    if 'name' in data:
        changes['name'] = _check_name(data['name'])
    if 'description' in data:
        changes['description'] = data['description']
    if 'color' in data:
        changes['color'] = _check_color(data['color'])
    return changes
