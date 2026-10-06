from datetime import datetime

from utils.constants import (
    DATE_FORMAT, DEFAULT_PRIORITY, DEFAULT_STATUS, MAX_PRIORITY, MAX_TITLE_LENGTH,
    MIN_PRIORITY, MIN_TITLE_LENGTH, TASK_STATUSES,
)
from utils.errors import ValidationError
from validators.common import is_int, optional_id, parse_int_param, require_object


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
    if not is_int(priority) or not MIN_PRIORITY <= priority <= MAX_PRIORITY:
        raise ValidationError(f'Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}')
    return priority


def _parse_date(value, message):
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError(message)


def _normalize_tags(tags):
    return ','.join(tags) if isinstance(tags, list) else tags


def validate_task_create(data):
    require_object(data)
    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')
    due_date = data.get('due_date')
    tags = data.get('tags')
    return {
        'title': _check_title(title),
        'description': data.get('description', ''),
        'status': _check_status(data.get('status', DEFAULT_STATUS)),
        'priority': _check_priority(data.get('priority', DEFAULT_PRIORITY)),
        'user_id': optional_id(data.get('user_id'), 'user_id'),
        'category_id': optional_id(data.get('category_id'), 'category_id'),
        'due_date': _parse_date(due_date, 'Formato de data inválido. Use YYYY-MM-DD') if due_date else None,
        'tags': _normalize_tags(tags) if tags else None,
    }


def validate_task_update(data):
    require_object(data)
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
        changes['user_id'] = optional_id(data['user_id'], 'user_id')
    if 'category_id' in data:
        changes['category_id'] = optional_id(data['category_id'], 'category_id')
    if 'due_date' in data:
        due_date = data['due_date']
        changes['due_date'] = _parse_date(due_date, 'Formato de data inválido') if due_date else None
    if 'tags' in data:
        changes['tags'] = _normalize_tags(data['tags'])
    return changes


def validate_search_filters(args):
    return {
        'text': args.get('q', ''),
        'status': args.get('status', ''),
        'priority': parse_int_param(args.get('priority', ''), 'priority'),
        'user_id': parse_int_param(args.get('user_id', ''), 'user_id'),
    }
