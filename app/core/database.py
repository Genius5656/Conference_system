"""Подключение к PostgreSQL и базовые классы ORM."""

from __future__ import annotations

from typing import Iterator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей приложения."""


def build_engine(database_url: Optional[str] = None) -> Engine:
    """Создаёт engine подключения к PostgreSQL.

    Args:
        database_url: SQLAlchemy-URL подключения. Если не указан, берётся
            из настроек приложения.

    Returns:
        Настроенный экземпляр :class:`sqlalchemy.engine.Engine`.
    """
    url = database_url or get_settings().database_url
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
        future=True,
    )


engine: Engine = build_engine()
"""Глобальный engine приложения."""

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
"""Фабрика сессий SQLAlchemy."""


def get_db() -> Iterator[Session]:
    """Зависимость FastAPI: сессия БД с автоматическим коммитом/откатом.

    Yields:
        Активная сессия SQLAlchemy.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine(database_url: str) -> Engine:
    """Пересоздаёт глобальный engine (используется тестами).

    Args:
        database_url: Новый SQLAlchemy-URL подключения.

    Returns:
        Новый экземпляр engine.
    """
    global engine, SessionLocal

    engine.dispose()
    engine = build_engine(database_url)
    SessionLocal.configure(bind=engine)
    return engine
