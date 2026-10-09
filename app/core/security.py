"""Хеширование паролей и работа с токенами доступа."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import jwt

from app.core.config import get_settings

ALGORITHM = "HS256"
TOKEN_SUBJECT_CLAIM = "sub"
TOKEN_ROLE_CLAIM = "role"


def hash_password(password: str) -> str:
    """Возвращает bcrypt-хеш пароля.

    Args:
        password: Открытый пароль пользователя.

    Returns:
        Строковый хеш, пригодный для хранения в БД.
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Проверяет пароль относительно сохранённого хеша.

    Args:
        password: Открытый пароль.
        password_hash: Хеш из базы данных.

    Returns:
        ``True`` при совпадении, иначе ``False``.
    """
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, role: str) -> str:
    """Создаёт подписанный JWT-токен сессии.

    Args:
        user_id: Идентификатор пользователя.
        role: Роль пользователя (``user`` / ``admin``).

    Returns:
        Строковый токен для httpOnly-куки.
    """
    settings = get_settings()
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=settings.token_ttl_minutes)
    payload: dict[str, Any] = {
        TOKEN_SUBJECT_CLAIM: str(user_id),
        TOKEN_ROLE_CLAIM: role,
        "iat": issued_at,
        "exp": expires_at,
        "iss": "conference-rf",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Декодирует и проверяет подпись токена сессии.

    Args:
        token: Значение httpOnly-куки.

    Returns:
        Полезная нагрузка токена либо ``None``, если токен недействителен.
    """
    try:
        return jwt.decode(
            token,
            get_settings().secret_key,
            algorithms=[ALGORITHM],
            issuer="conference-rf",
        )
    except jwt.PyJWTError:
        return None


def extract_user_id(payload: dict[str, Any]) -> Optional[int]:
    """Извлекает идентификатор пользователя из полезной нагрузки токена.

    Args:
        payload: Декодированный payload токена.

    Returns:
        Идентификатор пользователя либо ``None`` при ошибке данных.
    """
    raw_id = payload.get(TOKEN_SUBJECT_CLAIM)
    try:
        return int(raw_id)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
