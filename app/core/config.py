"""Конфигурация приложения.

Значения читаются из переменных окружения (приоритет) либо из файла `.env`
в корне проекта. Все обращения к настройкам выполняются через единую точку
доступа :func:`get_settings`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
"""Корневой каталог проекта ``conference_system``."""

STATIC_DIR = BASE_DIR / "app" / "static"
"""Каталог со статическими файлами веб-интерфейса."""

load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool) -> bool:
    """Читает булеву переменную окружения в непротиворечивом формате."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    """Читает целочисленную переменную окружения, безопасно для ``ValueError``."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Неизменяемый снимок настроек приложения."""

    name: str
    env: str
    debug: bool
    host: str
    port: int
    secret_key: str
    token_ttl_minutes: int
    cookie_name: str
    cookie_secure: bool
    database_url: str
    admin_login: str
    admin_password: str

    @property
    def is_production(self) -> bool:
        """Признак боевого окружения."""
        return self.env.lower() == "production"

    @property
    def static_dir(self) -> Path:
        """Путь к каталогу статических файлов веб-интерфейса."""
        return STATIC_DIR


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Возвращает кэшированный экземпляр настроек приложения."""
    return Settings(
        name=os.getenv("APP_NAME", "Конференции.РФ"),
        env=os.getenv("APP_ENV", "development"),
        debug=_env_bool("APP_DEBUG", True),
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=_env_int("APP_PORT", 8000),
        secret_key=os.getenv("APP_SECRET_KEY", "dev-secret-key-change-me"),
        token_ttl_minutes=_env_int("APP_TOKEN_TTL_MINUTES", 720),
        cookie_name="access_token",
        cookie_secure=_env_bool("APP_COOKIE_SECURE", False),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:postgres@localhost:5432/conference_system",
        ),
        admin_login=os.getenv("ADMIN_LOGIN", "Conf2027"),
        admin_password=os.getenv("ADMIN_PASSWORD", "Demo77"),
    )


def override_database_url(url: Optional[str]) -> None:
    """Переопределяет URL базы данных (используется тестами).

    Args:
        url: Новый SQLAlchemy-URL подключения либо ``None`` для отмены.
    """
    get_settings.cache_clear()
    if url is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = url
    get_settings.cache_clear()
