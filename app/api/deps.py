"""Общие зависимости FastAPI: аутентификация и контроль доступа."""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.enums import UserRole
from app.core.exceptions import AppError
from app.core.security import decode_access_token, extract_user_id
from app.models import User
from app.services import auth_service

UNAUTHORIZED_MESSAGE = "Требуется авторизация в системе"
SESSION_EXPIRED_MESSAGE = "Сессия истекла — войдите в систему заново"
FORBIDDEN_MESSAGE = "Доступ запрещён: требуется роль администратора"


def _user_from_request(request: Request, db: Session) -> Optional[User]:
    """Извлекает пользователя из httpOnly-куки сессии."""
    token = request.cookies.get(get_settings().cookie_name)
    if not token:
        return None

    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id = extract_user_id(payload)
    if user_id is None:
        return None

    return auth_service.get_user_by_id(db, user_id)


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Возвращает текущего пользователя или ``None``, если сессии нет.

    Args:
        request: HTTP-запрос.
        db: Сессия базы данных.

    Returns:
        Пользователь либо ``None``.
    """
    return _user_from_request(request, db)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Требует авторизованного пользователя.

    Args:
        request: HTTP-запрос.
        db: Сессия базы данных.

    Returns:
        Текущий пользователь.

    Raises:
        AppError: 401 — сессия отсутствует, истекла или недействительна.
    """
    token = request.cookies.get(get_settings().cookie_name)
    if not token:
        raise AppError(
            UNAUTHORIZED_MESSAGE,
            status_code=401,
            code="unauthorized",
        )

    user = _user_from_request(request, db)
    if user is None:
        raise AppError(
            SESSION_EXPIRED_MESSAGE,
            status_code=401,
            code="session_expired",
        )
    return user


def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Требует пользователя с ролью администратора.

    Args:
        user: Текущий пользователь.

    Returns:
        Пользователь-администратор.

    Raises:
        AppError: 403 — у пользователя нет прав администратора.
    """
    if user.role is not UserRole.ADMIN:
        raise AppError(
            FORBIDDEN_MESSAGE,
            status_code=403,
            code="forbidden",
        )
    return user
