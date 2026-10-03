from database import PersistenceMixin, db, transaction
from utils.constants import DEFAULT_COLOR
from utils.helpers import utcnow


class Category(PersistenceMixin, db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': str(self.created_at),
        }

    def delete_detaching_tasks(self):
        """Delete the category and clear category_id of its tasks in one transaction."""
        from models.task import Task

        with transaction() as session:
            session.execute(
                db.update(Task).where(Task.category_id == self.id).values(category_id=None)
            )
            session.delete(self)
