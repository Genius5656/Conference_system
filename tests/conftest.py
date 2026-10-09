"""Общие фикстуры для интеграционных тестов API портала.

Тесты выполняются against реальной PostgreSQL, URL которой задан переменной
окружения ``DATABASE_URL``. Перед каждым тестом схема пересоздаётся с нуля,
поэтому набор тестов детерминирован и не зависит от состояния базы.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Callable, Dict

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app

REGISTRATION_PAYLOAD: Dict[str, Any] = {
    "login": "ivanov2027",
    "password": "password123",
    "full_name": "Иванов Иван Иванович",
    "phone": "8(999)123-45-67",
    "email": "ivanov@example.ru",
}

ADMIN_CREDENTIALS: Dict[str, str] = {
    "login": "Conf2027",
    "password": "Demo77",
}


def future_date(days: int = 30) -> str:
    """Возвращает дату в будущем в формате ISO.

    Args:
        days: Сколько дней прибавить к сегодняшней дате.

    Returns:
        Дата в формате ``ГГГГ-ММ-ДД``.
    """
    return (date.today() + timedelta(days=days)).isoformat()


def register_user(client: TestClient, **overrides: Any) -> Dict[str, Any]:
    """Регистрирует пользователя и возвращает его профиль.

    Args:
        client: HTTP-клиент.
        **overrides: Переопределение полей регистрации.

    Returns:
        Профиль созданного пользователя.
    """
    payload = dict(REGISTRATION_PAYLOAD)
    payload.update(overrides)
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture(autouse=True)
def clean_db():
    """Пересоздаёт схему тестовой базы данных перед каждым тестом."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(clean_db) -> TestClient:
    """Основной HTTP-клиент с запущенным лайфсайклом приложения."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def new_client(clean_db) -> Callable[[], TestClient]:
    """Фабрика дополнительных клиентов с независимыми сессиями cookies.

    Returns:
        Функция, создающая новый HTTP-клиент.
    """
    clients = []

    def factory() -> TestClient:
        test_client = TestClient(app)
        test_client.__enter__()
        clients.append(test_client)
        return test_client

    yield factory

    for test_client in clients:
        test_client.__exit__(None, None, None)


@pytest.fixture()
def user_client(client: TestClient) -> TestClient:
    """Клиент, авторизованный под обычным пользователем."""
    register_user(client)
    return client


@pytest.fixture()
def admin_client(client: TestClient) -> TestClient:
    """Клиент, авторизованный под администратором портала."""
    response = client.post("/api/auth/login", json=ADMIN_CREDENTIALS)
    assert response.status_code == 200, response.text
    return client
