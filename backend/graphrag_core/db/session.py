"""Database engine and session helpers."""

from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config.settings import settings
from backend.graphrag_core.db.base import Base


def _build_engine() -> Engine:
    connect_args: dict[str, object] = {}
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(
        settings.DATABASE_URL,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    """Create database tables if they do not exist."""

    import backend.graphrag_core.models.persistence  # noqa: F401

    Base.metadata.create_all(bind=engine)


@contextmanager
def db_session() -> Session:
    """Provide a transactional SQLAlchemy session."""

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
