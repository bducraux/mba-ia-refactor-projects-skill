from utils.constants import DEFAULT_ROLE, MIN_PASSWORD_LENGTH, USER_ROLES
from utils.errors import ValidationError
from utils.helpers import is_valid_email

INVALID_PAYLOAD = 'Dados inválidos'


def _require_payload(data):
    if not data or not isinstance(data, dict):
        raise ValidationError(INVALID_PAYLOAD)


def _check_email(email):
    if not is_valid_email(email):
        raise ValidationError('Email inválido')
    return email


def _check_password(password, message):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(message)
    return password


def _check_role(role):
    if role not in USER_ROLES:
        raise ValidationError('Role inválido')
    return role


def _check_name(name):
    if not name or not isinstance(name, str):
        raise ValidationError('Nome é obrigatório')
    return name


def validate_user_create(data):
    _require_payload(data)
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    return {
        'name': _check_name(name),
        'email': _check_email(email),
        'password': _check_password(password, f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres'),
        'role': data.get('role', DEFAULT_ROLE),
    }


def validate_role(role):
    return _check_role(role)


def validate_user_update(data):
    _require_payload(data)
    changes = {}
    if 'name' in data:
        changes['name'] = _check_name(data['name'])
    if 'email' in data:
        changes['email'] = _check_email(data['email'])
    if 'password' in data:
        changes['password'] = _check_password(data['password'], 'Senha muito curta')
    if 'role' in data:
        changes['role'] = _check_role(data['role'])
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Campo active inválido')
        changes['active'] = data['active']
    return changes


def validate_login(data):
    _require_payload(data)
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    return {'email': email, 'password': password}
