import re

from utils.constants import DEFAULT_ROLE, EMAIL_PATTERN, MIN_PASSWORD_LENGTH, USER_ROLES
from utils.errors import ValidationError
from validators.common import require_object

_EMAIL_RE = re.compile(EMAIL_PATTERN)


def _check_email(email):
    if not isinstance(email, str) or not _EMAIL_RE.match(email):
        raise ValidationError('Email inválido')
    return email


def _check_role(role):
    if role not in USER_ROLES:
        raise ValidationError('Role inválido')
    return role


def _password_ok(password):
    return isinstance(password, str) and len(password) >= MIN_PASSWORD_LENGTH


def validate_user_create(data):
    require_object(data)
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    if not name or not isinstance(name, str):
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    _check_email(email)
    if not _password_ok(password):
        raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
    return {
        'name': name,
        'email': email,
        'password': password,
        'role': _check_role(data.get('role', DEFAULT_ROLE)),
    }


def validate_user_update(data):
    require_object(data)
    changes = {}
    if 'name' in data:
        if not data['name'] or not isinstance(data['name'], str):
            raise ValidationError('Nome é obrigatório')
        changes['name'] = data['name']
    if 'email' in data:
        changes['email'] = _check_email(data['email'])
    if 'password' in data:
        if not _password_ok(data['password']):
            raise ValidationError('Senha muito curta')
        changes['password'] = data['password']
    if 'role' in data:
        changes['role'] = _check_role(data['role'])
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Campo active deve ser booleano')
        changes['active'] = data['active']
    return changes


def validate_login(data):
    require_object(data)
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    return email, password
