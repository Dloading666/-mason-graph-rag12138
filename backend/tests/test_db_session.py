"""Database session helpers."""

from __future__ import annotations

from backend.graphrag_core.db import session as db_session


def test_build_engine_supports_sqlite(monkeypatch):
    monkeypatch.setattr(db_session.settings, "DATABASE_URL", "sqlite:///backend/data/state/test.db")

    engine = db_session._build_engine()

    try:
        assert engine.dialect.name == "sqlite"
    finally:
        engine.dispose()


def test_build_engine_supports_mysql(monkeypatch):
    monkeypatch.setattr(
        db_session.settings,
        "DATABASE_URL",
        "mysql+pymysql://mason:mason_password@localhost:3306/mason_graph_rag?charset=utf8mb4",
    )

    engine = db_session._build_engine()

    try:
        assert engine.dialect.name == "mysql"
    finally:
        engine.dispose()
