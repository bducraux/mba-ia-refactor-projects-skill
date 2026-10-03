from contextlib import contextmanager

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


@contextmanager
def transaction():
    """Commit everything done inside the block, or roll it all back on error."""
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


class PersistenceMixin:
    @classmethod
    def find(cls, entity_id):
        return db.session.get(cls, entity_id)

    @classmethod
    def list_all(cls):
        return db.session.execute(db.select(cls).order_by(cls.id)).scalars().all()

    @classmethod
    def count_all(cls):
        return db.session.execute(db.select(db.func.count()).select_from(cls)).scalar_one()

    def save(self):
        with transaction() as session:
            session.add(self)
        return self

    def delete(self):
        with transaction() as session:
            session.delete(self)
