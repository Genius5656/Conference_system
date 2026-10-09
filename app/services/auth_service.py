"""Регистрация и аутентификация пользователей."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.exceptions import AppError
from app.core.security import hash_password, verify_password
from app.models import User
from app.schemas.auth import UserCreate

LOGIN_TAKEN_MESSAGE = "Пользователь с таким логином уже существует"
INVALID_CREDENTIALS_MESSAGE = "Неверный логин или пароль"


def get_user_by_login(db: Session, login: str) -> User | None:
    """Возвращает пользователя по логину.

    Args:
        db: Сессия базы данных.
        login: Логин пользователя.

    Returns:
        Пользователь или ``None``, если запись не найдена.
    """
    return db.scalar(select(User).where(User.login == login))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Возвращает пользователя по идентификатору.

    Args:
        db: Сессия базы данных.
        user_id: Идентификатор пользователя.

    Returns:
        Пользователь или ``None``, если запись не найдена.
    """
    return db.get(User, user_id)


def register_user(db: Session, payload: UserCreate) -> User:
    """Создаёт нового пользователя портала.

    Args:
        db: Сессия базы данных.
        payload: Валидированные данные формы регистрации.

    Returns:
        Созданный пользователь.

    Raises:
        AppError: Если логин уже занят (409).
    """
    if get_user_by_login(db, payload.login) is not None:
        raise AppError(
            LOGIN_TAKEN_MESSAGE,
            status_code=409,
            errors={"login": LOGIN_TAKEN_MESSAGE},
            code="login_taken",
        )

    user = User(
        login=payload.login,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        role=UserRole.USER,
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def authenticate(db: Session, login: str, password: str) -> User:
    """Проверяет учётные данные пользователя.

    Args:
        db: Сессия базы данных.
        login: Логин пользователя.
        password: Пароль в открытом виде.

    Returns:
        Аутентифицированный пользователь.

    Raises:
        AppError: Если логин или пароль неверны (401).
    """
    user = get_user_by_login(db, login)
    if user is None or not verify_password(password, user.password_hash):
        raise AppError(
            INVALID_CREDENTIALS_MESSAGE,
            status_code=401,
            errors={"login": INVALID_CREDENTIALS_MESSAGE},
            code="invalid_credentials",
        )
    return user
