from sqlalchemy.orm import joinedload

from database import PersistenceMixin, db
from utils.constants import CLOSED_STATUSES, DEFAULT_PRIORITY, STATUS_DONE, STATUS_PENDING, TAG_SEPARATOR
from utils.helpers import format_date, utcnow


class Task(PersistenceMixin, db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    # --- serialization -----------------------------------------------------

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
            'due_date': format_date(self.due_date),
            'tags': self.tags.split(TAG_SEPARATOR) if self.tags else [],
        }

    def to_summary_dict(self, now=None):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': format_date(self.due_date),
            'overdue': self.is_overdue(now),
        }

    # --- domain rule -------------------------------------------------------

    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date) and self.due_date < now and self.status not in CLOSED_STATUSES

    # --- queries -----------------------------------------------------------

    @classmethod
    def _overdue_clause(cls, now):
        return db.and_(cls.due_date.is_not(None), cls.due_date < now, cls.status.not_in(CLOSED_STATUSES))

    @classmethod
    def list_with_relations(cls):
        query = (
            db.select(cls)
            .options(joinedload(cls.user), joinedload(cls.category))
            .order_by(cls.id)
        )
        return db.session.execute(query).scalars().all()

    @classmethod
    def find_by_user(cls, user_id):
        query = db.select(cls).filter_by(user_id=user_id).order_by(cls.id)
        return db.session.execute(query).scalars().all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        query = db.select(cls)
        if text:
            pattern = f'%{text}%'
            query = query.where(db.or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            query = query.where(cls.status == status)
        if priority is not None:
            query = query.where(cls.priority == priority)
        if user_id is not None:
            query = query.where(cls.user_id == user_id)
        return db.session.execute(query.order_by(cls.id)).scalars().all()

    @classmethod
    def _grouped_counts(cls, column):
        query = db.select(column, db.func.count()).group_by(column)
        return dict(db.session.execute(query).all())

    @classmethod
    def count_by_status(cls):
        return cls._grouped_counts(cls.status)

    @classmethod
    def count_by_priority(cls):
        return cls._grouped_counts(cls.priority)

    @classmethod
    def count_by_category(cls):
        return cls._grouped_counts(cls.category_id)

    @classmethod
    def count_by_user(cls):
        """{user_id: (total_tasks, done_tasks)} in a single GROUP BY query."""
        done = db.func.sum(db.case((cls.status == STATUS_DONE, 1), else_=0))
        query = db.select(cls.user_id, db.func.count(), done).group_by(cls.user_id)
        return {user_id: (total, done or 0) for user_id, total, done in db.session.execute(query).all()}

    @classmethod
    def count_overdue(cls, now):
        query = db.select(db.func.count()).select_from(cls).where(cls._overdue_clause(now))
        return db.session.execute(query).scalar_one()

    @classmethod
    def list_overdue(cls, now):
        query = db.select(cls).where(cls._overdue_clause(now)).order_by(cls.id)
        return db.session.execute(query).scalars().all()

    @classmethod
    def count_created_since(cls, since):
        query = db.select(db.func.count()).select_from(cls).where(cls.created_at >= since)
        return db.session.execute(query).scalar_one()

    @classmethod
    def count_completed_since(cls, since):
        query = (
            db.select(db.func.count())
            .select_from(cls)
            .where(cls.status == STATUS_DONE, cls.updated_at >= since)
        )
        return db.session.execute(query).scalar_one()
