from database import db, transaction


class PersistenceMixin:
    """Data access shared by every entity."""

    @classmethod
    def get(cls, entity_id):
        return db.session.get(cls, entity_id)

    @classmethod
    def list_all(cls):
        return db.session.scalars(db.select(cls).order_by(cls.id)).all()

    @classmethod
    def count(cls):
        return db.session.scalar(db.select(db.func.count()).select_from(cls))

    def save(self):
        with transaction() as session:
            session.add(self)
        return self

    def delete(self):
        with transaction() as session:
            session.delete(self)
