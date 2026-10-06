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
