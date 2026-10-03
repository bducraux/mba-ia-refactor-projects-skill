import re
from datetime import datetime, timezone

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


def utcnow():
    """Current UTC time as a naive datetime (same format as the values already stored)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_date(value):
    return str(value) if value else None


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def is_valid_email(email):
    return isinstance(email, str) and EMAIL_PATTERN.match(email) is not None


def is_valid_color(color):
    return isinstance(color, str) and COLOR_PATTERN.match(color) is not None
