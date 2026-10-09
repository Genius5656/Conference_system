"""Фабрика FastAPI-приложения портала «Конференции.РФ»."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.db import bootstrap_database

LOGGER = logging.getLogger("conference_rf")


def configure_logging(debug: bool = False) -> None:
    """Настраивает логирование приложения.

    Args:
        debug: Признак включения отладочного уровня логирования.
    """
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Лайфсайкл приложения: инициализация БД перед началом приёма запросов.

    Args:
        app: Экземпляр FastAPI-приложения.

    Yields:
        Управление приложением во время работы.
    """
    settings = get_settings()
    configure_logging(settings.debug)
    LOGGER.info("Инициализация базы данных…")
    bootstrap_database()
    LOGGER.info(
        "Приложение запущено: %s (env=%s, db=%s)",
        settings.name,
        settings.env,
        settings.database_url.split("@")[-1],
    )
    yield
    LOGGER.info("Остановка приложения")


def register_middlewares(app: FastAPI) -> None:
    """Регистрирует служебные middleware приложения.

    Args:
        app: Экземпляр FastAPI-приложения.
    """

    @app.middleware("http")
    async def security_headers(request: Request, call_next):  # noqa: ANN001
        """Добавляет базовые заголовки безопасности к каждому ответу."""
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        return response


def create_app(static_dir: Optional[str] = None) -> FastAPI:
    """Создаёт экземпляр FastAPI-приложения.

    Args:
        static_dir: Переопределение каталога статических файлов.

    Returns:
        Настроенное приложение.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.name,
        version=__version__,
        description=(
            "Информационная система бронирования помещений для проведения "
            "Всероссийских конференций: аудитории, коворкинги и кинозалы."
        ),
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    register_exception_handlers(app)
    register_middlewares(app)
    app.include_router(api_router)

    directory = static_dir or str(settings.static_dir)
    app.mount("/", StaticFiles(directory=directory, html=True), name="static")
    return app


app = create_app()
"""Глобальное экземпляр приложения (точка входа для uvicorn)."""


def main() -> None:
    """Запуск приложения через ``python -m app.main``."""
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
