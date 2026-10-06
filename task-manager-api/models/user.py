from database import db, transaction
from models.base import PersistenceMixin
from models.task import Task
from utils.constants import DEFAULT_ROLE, ROLE_ADMIN
from utils.helpers import utcnow
from utils.security import hash_password, is_legacy_hash, verify_password


class User(PersistenceMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        """Public representation: never includes the password hash."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, raw_password):
        self.password = hash_password(raw_password)

    def check_password(self, raw_password):
        return verify_password(self.password, raw_password)

    def has_legacy_password_hash(self):
        return is_legacy_hash(self.password)

    def is_admin(self):
        return self.role == ROLE_ADMIN

    @classmethod
    def get_by_email(cls, email):
        return db.session.scalars(db.select(cls).filter_by(email=email)).first()

    def delete_with_tasks(self):
        """Delete the user and every task assigned to them in one transaction."""
        with transaction() as session:
            session.execute(db.delete(Task).where(Task.user_id == self.id))
            session.delete(self)
