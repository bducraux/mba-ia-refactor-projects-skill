from datetime import datetime

from utils.constants import (
    DEFAULT_PRIORITY,
    DUE_DATE_FORMAT,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    STATUS_PENDING,
    TAG_SEPARATOR,
    TASK_STATUSES,
)
from utils.errors import ValidationError

INVALID_PAYLOAD = 'Dados inválidos'
CREATE_DATE_ERROR = 'Formato de data inválido. Use YYYY-MM-DD'
UPDATE_DATE_ERROR = 'Formato de data inválido'


def _require_payload(data):
    if not data or not isinstance(data, dict):
        raise ValidationError(INVALID_PAYLOAD)


def _check_title(title):
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def _check_status(status):
    if status not in TASK_STATUSES:
        raise ValidationError('Status inválido')
    return status


def _check_priority(priority):
    is_int = isinstance(priority, int) and not isinstance(priority, bool)
    if not is_int or not MIN_PRIORITY <= priority <= MAX_PRIORITY:
        raise ValidationError(f'Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}')
    return priority


def _parse_due_date(value, error_message):
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError(error_message)


def _normalize_tags(tags):
    if isinstance(tags, list):
        if not all(isinstance(tag, str) for tag in tags):
            raise ValidationError('Tags inválidas')
        return TAG_SEPARATOR.join(tags)
    if tags is None or isinstance(tags, str):
        return tags
    raise ValidationError('Tags inválidas')


def validate_task_create(data):
    _require_payload(data)
    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')

    due_date = data.get('due_date')
    tags = data.get('tags')
    return {
        'title': _check_title(title),
        'description': data.get('description', ''),
        'status': _check_status(data.get('status', STATUS_PENDING)),
        'priority': _check_priority(data.get('priority', DEFAULT_PRIORITY)),
        'user_id': data.get('user_id'),
        'category_id': data.get('category_id'),
        'due_date': _parse_due_date(due_date, CREATE_DATE_ERROR) if due_date else None,
        'tags': _normalize_tags(tags) if tags else None,
    }


def validate_task_update(data):
    """Return only the fields present in the payload, validated and normalized."""
    _require_payload(data)
    changes = {}
    if 'title' in data:
        changes['title'] = _check_title(data['title'])
    if 'description' in data:
        changes['description'] = data['description']
    if 'status' in data:
        changes['status'] = _check_status(data['status'])
    if 'priority' in data:
        changes['priority'] = _check_priority(data['priority'])
    if 'user_id' in data:
        changes['user_id'] = data['user_id']
    if 'category_id' in data:
        changes['category_id'] = data['category_id']
    if 'due_date' in data:
        due_date = data['due_date']
        changes['due_date'] = _parse_due_date(due_date, UPDATE_DATE_ERROR) if due_date else None
    if 'tags' in data:
        changes['tags'] = _normalize_tags(data['tags'])
    return changes


def _optional_int(value, error_message):
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(error_message)


def validate_search_params(args):
    return {
        'text': args.get('q', ''),
        'status': args.get('status', ''),
        'priority': _optional_int(args.get('priority', ''), 'Prioridade inválida'),
        'user_id': _optional_int(args.get('user_id', ''), 'Usuário inválido'),
    }
