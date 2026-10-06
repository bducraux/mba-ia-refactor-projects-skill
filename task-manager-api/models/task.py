from sqlalchemy.orm import selectinload

from database import db
from models.base import PersistenceMixin
from utils.constants import CLOSED_STATUSES, DEFAULT_PRIORITY, DEFAULT_STATUS, STATUS_DONE
from utils.helpers import utcnow


class Task(PersistenceMixin, db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }

    def is_overdue(self, now=None):
        if not self.due_date or self.status in CLOSED_STATUSES:
            return False
        return self.due_date < (now or utcnow())

    # ---- queries -------------------------------------------------------

    @staticmethod
    def _overdue_clause(now):
        return db.and_(
            Task.due_date.is_not(None),
            Task.due_date < now,
            Task.status.not_in(CLOSED_STATUSES),
        )

    @classmethod
    def list_with_relations(cls):
        stmt = db.select(cls).options(selectinload(cls.user), selectinload(cls.category)).order_by(cls.id)
        return db.session.scalars(stmt).all()

    @classmethod
    def list_by_user(cls, user_id):
        return db.session.scalars(db.select(cls).filter_by(user_id=user_id).order_by(cls.id)).all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        stmt = db.select(cls)
        if text:
            pattern = f'%{text}%'
            stmt = stmt.where(db.or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            stmt = stmt.where(cls.status == status)
        if priority is not None:
            stmt = stmt.where(cls.priority == priority)
        if user_id is not None:
            stmt = stmt.where(cls.user_id == user_id)
        return db.session.scalars(stmt.order_by(cls.id)).all()

    @classmethod
    def list_overdue(cls, now):
        return db.session.scalars(db.select(cls).where(cls._overdue_clause(now)).order_by(cls.id)).all()

    @classmethod
    def count_overdue(cls, now):
        return db.session.scalar(db.select(db.func.count(cls.id)).where(cls._overdue_clause(now)))

    @classmethod
    def count_by_status(cls):
        rows = db.session.execute(db.select(cls.status, db.func.count(cls.id)).group_by(cls.status))
        return {status: total for status, total in rows}

    @classmethod
    def count_by_priority(cls):
        rows = db.session.execute(db.select(cls.priority, db.func.count(cls.id)).group_by(cls.priority))
        return {priority: total for priority, total in rows}

    @classmethod
    def count_by_user(cls):
        """{user_id: (total_tasks, done_tasks)} in a single grouped query."""
        done = db.func.sum(db.case((cls.status == STATUS_DONE, 1), else_=0))
        rows = db.session.execute(
            db.select(cls.user_id, db.func.count(cls.id), done).where(cls.user_id.is_not(None)).group_by(cls.user_id)
        )
        return {user_id: (total, int(done_count or 0)) for user_id, total, done_count in rows}

    @classmethod
    def count_by_category(cls):
        rows = db.session.execute(
            db.select(cls.category_id, db.func.count(cls.id)).where(cls.category_id.is_not(None)).group_by(cls.category_id)
        )
        return {category_id: total for category_id, total in rows}

    @classmethod
    def count_created_since(cls, since):
        return db.session.scalar(db.select(db.func.count(cls.id)).where(cls.created_at >= since))

    @classmethod
    def count_completed_since(cls, since):
        return db.session.scalar(
            db.select(db.func.count(cls.id)).where(cls.status == STATUS_DONE, cls.updated_at >= since)
        )
