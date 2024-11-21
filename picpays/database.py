import contextvars
from functools import wraps

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from picpays.settings import Settings

engine = create_engine(Settings().DATABASE_URL)  # type:ignore


def get_session():
    with Session(engine) as session:
        yield session


db_session_context = contextvars.ContextVar('session', default=None)


def transactional(func):
    @wraps(func)
    def wrap_func(*args, **kwargs):
        db_session = db_session_context.get()
        if db_session:
            return func(*args, **kwargs)
        db_session = Session(engine)
        db_session_context.set(db_session)
        try:
            result = func(*args, **kwargs)
            db_session.refresh(result)
            db_session.commit()
        except Exception:
            db_session.rollback()
        finally:
            db_session.close()
            db_session_context.set(None)
        return result

    return wrap_func
