"""Маршруты регистрации, входа и выхода из системы."""

from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.models import User
from app.schemas.auth import UserCreate, UserLogin, UserOut
from app.services import auth_service

router = APIRouter()


def _open_session(response: Response, user: User) -> None:
    """Выставляет httpOnly-куку с токеном сессии."""
    settings = get_settings()
    response.set_cookie(
        key=settings.cookie_name,
        value=create_access_token(user.id, user.role.value),
        max_age=settings.token_ttl_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
)
def register(
    payload: UserCreate,
    response: Response,
    db: Session = Depends(get_db),
) -> UserOut:
    """Создаёт пользователя и открывает сессию.

    Args:
        payload: Данные формы регистрации.
        response: HTTP-ответ для выставления куки.
        db: Сессия базы данных.

    Returns:
        Созданный пользователь.
    """
    user = auth_service.register_user(db, payload)
    _open_session(response, user)
    return UserOut.model_validate(user)


@router.post(
    "/login",
    response_model=UserOut,
    summary="Авторизация пользователя",
)
def login(
    payload: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
) -> UserOut:
    """Проверяет учётные данные и открывает сессию.

    Args:
        payload: Логин и пароль.
        response: HTTP-ответ для выставления куки.
        db: Сессия базы данных.

    Returns:
        Аутентифицированный пользователь.
    """
    user = auth_service.authenticate(db, payload.login, payload.password)
    _open_session(response, user)
    return UserOut.model_validate(user)


@router.post(
    "/logout",
    summary="Завершение сессии",
)
def logout(response: Response) -> Dict[str, str]:
    """Удаляет куку сессии.

    Args:
        response: HTTP-ответ для удаления куки.

    Returns:
        Подтверждение выхода.
    """
    response.delete_cookie(
        key=get_settings().cookie_name,
        path="/",
        samesite="lax",
        secure=get_settings().cookie_secure,
    )
    return {"message": "Выход выполнен"}


@router.get(
    "/me",
    response_model=UserOut,
    summary="Текущий авторизованный пользователь",
)
def me(user: User = Depends(get_current_user)) -> UserOut:
    """Возвращает профиль текущего пользователя.

    Args:
        user: Текущий пользователь из куки сессии.

    Returns:
        Профиль пользователя.
    """
    return UserOut.model_validate(user)
