from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from database import PersistenceMixin, db, transaction
from utils.constants import ROLE_ADMIN, ROLE_USER
from utils.errors import ConflictError
from utils.helpers import utcnow

DUPLICATE_EMAIL_MESSAGE = 'Email já cadastrado'


class User(PersistenceMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        """Public representation: the password hash is never exposed."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    def is_admin(self):
        return self.role == ROLE_ADMIN

    @classmethod
    def find_by_email(cls, email):
        return db.session.execute(db.select(cls).filter_by(email=email)).scalar_one_or_none()

    def save(self):
        try:
            return super().save()
        except IntegrityError as exc:
            raise ConflictError(DUPLICATE_EMAIL_MESSAGE) from exc

    def delete_with_tasks(self):
        """Delete the user and all tasks assigned to them in one transaction."""
        from models.task import Task

        with transaction() as session:
            session.execute(db.delete(Task).where(Task.user_id == self.id))
            session.delete(self)
