import hashlib
import hmac
import re

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

_LEGACY_MD5 = re.compile(r'^[0-9a-f]{32}$')


def hash_password(raw):
    return generate_password_hash(raw)


def is_legacy_hash(stored):
    return bool(stored and _LEGACY_MD5.match(stored))


def verify_password(stored, raw):
    if not stored:
        return False
    if is_legacy_hash(stored):
        # Hashes created before the refactor; verified once and upgraded on login.
        return hmac.compare_digest(stored, hashlib.md5(raw.encode()).hexdigest())
    return check_password_hash(stored, raw)


class TokenSigner:
    def __init__(self, secret_key, max_age_seconds):
        self._serializer = URLSafeTimedSerializer(secret_key, salt='auth-token')
        self._max_age = max_age_seconds

    def sign(self, user_id):
        return self._serializer.dumps({'uid': user_id})

    def read(self, token):
        """Return the user id in the token, or None if it is invalid or expired."""
        try:
            data = self._serializer.loads(token, max_age=self._max_age)
        except (BadSignature, SignatureExpired):
            return None
        return data.get('uid') if isinstance(data, dict) else None
