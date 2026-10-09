"""Интеграционные тесты REST API портала «Конференции.РФ»."""

from __future__ import annotations

from typing import Any, Callable, Dict

import pytest
from fastapi.testclient import TestClient

from tests.conftest import (
    ADMIN_CREDENTIALS,
    REGISTRATION_PAYLOAD,
    future_date,
    register_user,
)


# ---------------------------------------------------------------------------
# Служебные маршруты и справочники
# ---------------------------------------------------------------------------


def test_health_reports_database_availability(client: TestClient) -> None:
    """Эндпоинт /api/health отвечает и подтверждает доступность БД."""
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "ok"


def test_rooms_catalog_is_seeded(client: TestClient) -> None:
    """Каталог помещений наполнен стартовыми данными."""
    response = client.get("/api/rooms")

    assert response.status_code == 200
    rooms = response.json()
    assert len(rooms) == 5
    kinds = {room["kind"] for room in rooms}
    assert kinds == {"auditorium", "coworking", "cinema"}


# ---------------------------------------------------------------------------
# Регистрация
# ---------------------------------------------------------------------------


def test_registration_creates_user_and_opens_session(client: TestClient) -> None:
    """По кнопке «Создать пользователя» данные попадают в БД, сессия открыта."""
    response = client.post("/api/auth/register", json=REGISTRATION_PAYLOAD)

    assert response.status_code == 201
    user = response.json()
    assert user["login"] == "ivanov2027"
    assert user["role"] == "user"
    assert "password" not in user
    assert "password_hash" not in user

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["login"] == "ivanov2027"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("login", "abc"),
        ("login", "иванов2027"),
        ("password", "short"),
        ("full_name", "Ivanov Ivan"),
        ("full_name", "Иванов-Иванов"),
        ("phone", "+7 (999) 123-45-67"),
        ("phone", "89991234567"),
        ("email", "not-an-email"),
    ],
)
def test_registration_rejects_invalid_fields(
    client: TestClient, field: str, value: str
) -> None:
    """Некорректные данные отклоняются с сообщением по конкретному полю."""
    payload: Dict[str, Any] = dict(REGISTRATION_PAYLOAD)
    payload[field] = value

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 422
    errors = response.json()["errors"]
    assert field in errors
    assert errors[field]


def test_registration_requires_every_field(client: TestClient) -> None:
    """Все поля формы регистрации обязательны."""
    response = client.post("/api/auth/register", json={})

    assert response.status_code == 422
    errors = response.json()["errors"]
    assert set(errors) == {"login", "password", "full_name", "phone", "email"}


def test_registration_normalizes_full_name_and_email(client: TestClient) -> None:
    """Лишние пробелы в ФИО схлопываются, почта приводится к нижнему регистру."""
    payload = dict(
        REGISTRATION_PAYLOAD,
        full_name="  Иванова   Мария   Сергеевна ",
        email="Maria.Ivanova@Example.RU",
    )

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 201
    user = response.json()
    assert user["full_name"] == "Иванова Мария Сергеевна"
    assert user["email"] == "maria.ivanova@example.ru"


def test_duplicate_login_returns_conflict(client: TestClient) -> None:
    """Повторный логин блокируется: 409 и ошибка по полю login."""
    register_user(client)

    response = client.post(
        "/api/auth/register", json=dict(REGISTRATION_PAYLOAD, email="other@example.ru")
    )

    assert response.status_code == 409
    assert response.json()["errors"]["login"]


# ---------------------------------------------------------------------------
# Авторизация
# ---------------------------------------------------------------------------


def test_login_with_wrong_password_returns_401(client: TestClient) -> None:
    """Неверный пароль — понятное сообщение об ошибке и код 401."""
    register_user(client)
    client.post("/api/auth/logout")

    response = client.post(
        "/api/auth/login",
        json={"login": REGISTRATION_PAYLOAD["login"], "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert "логин или пароль" in response.json()["message"].lower()


def test_logout_clears_session(client: TestClient) -> None:
    """После выхода текущий пользователь больше недоступен."""
    register_user(client)

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200

    assert client.get("/api/auth/me").status_code == 401


def test_protected_routes_require_authentication(client: TestClient) -> None:
    """Без сессии защищённые маршруты отвечают 401."""
    assert client.get("/api/bookings").status_code == 401
    assert client.post("/api/bookings", json={}).status_code == 401


def test_admin_credentials_from_task_are_accepted(client: TestClient) -> None:
    """Панель администратора открывается по логину Conf2027 / паролю Demo77."""
    response = client.post("/api/auth/login", json=ADMIN_CREDENTIALS)

    assert response.status_code == 200
    user = response.json()
    assert user["role"] == "admin"
    assert user["login"] == "Conf2027"

    stats = client.get("/api/admin/stats")
    assert stats.status_code == 200
    assert stats.json()["users"] == 0


def test_regular_user_cannot_open_admin_panel(
    new_client: Callable[[], TestClient]  # type: ignore[name-defined]
) -> None:
    """Обычный пользователь получает 403 на админ-маршрутах."""
    user_session = new_client()
    register_user(user_session)

    assert user_session.get("/api/admin/bookings").status_code == 403
    assert user_session.get("/api/admin/stats").status_code == 403


# ---------------------------------------------------------------------------
# Заявки
# ---------------------------------------------------------------------------


def booking_payload(**overrides: Any) -> Dict[str, Any]:  # type: ignore[name-defined]
    """Возвращает корректное тело запроса на создание заявки."""
    payload: Dict[str, Any] = {
        "room_id": 1,
        "event_date": future_date(),
        "start_time": "10:30",
        "payment_method": "sbp",
    }
    payload.update(overrides)
    return payload


def test_user_creates_and_lists_own_bookings(user_client: TestClient) -> None:
    """Заявка создаётся со статусом «Новая» и попадает в личный кабинет."""
    response = user_client.post("/api/bookings", json=booking_payload())

    assert response.status_code == 201
    booking = response.json()
    assert booking["status"] == "new"
    assert booking["status_label"] == "Новая"
    assert booking["payment_method_label"] == "Перевод по системе СБП"
    assert booking["can_review"] is False

    listed = user_client.get("/api/bookings")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_booking_supports_custom_room_name(user_client: TestClient) -> None:
    """Пользователь может ввести название помещения вне справочника."""
    payload = booking_payload(
        room_id=None,
        room_name="Актовый зал колледжа",
        payment_method="onsite",
    )

    response = user_client.post("/api/bookings", json=payload)

    assert response.status_code == 201
    booking = response.json()
    assert booking["room_id"] is None
    assert booking["room_name"] == "Актовый зал колледжа"
    assert booking["payment_method_label"] == "При очном посещении"


def test_booking_requires_selected_room(user_client: TestClient) -> None:
    """Без выбранного помещения заявка не создаётся."""
    payload = booking_payload(room_id=None, room_name=None)

    response = user_client.post("/api/bookings", json=payload)

    assert response.status_code == 400
    assert response.json()["errors"]["room_id"]


@pytest.mark.parametrize("field,value", [("payment_method", "cash"), ("payment_method", "")])
def test_booking_rejects_unknown_payment_method(
    user_client: TestClient, field: str, value: str
) -> None:
    """Способ оплаты выбирается только из предложенного списка."""
    response = user_client.post("/api/bookings", json=booking_payload(**{field: value}))

    assert response.status_code == 422
    assert field in response.json()["errors"]


def test_booking_rejects_past_date(user_client: TestClient) -> None:
    """Дата конференции не может быть в прошлом."""
    response = user_client.post(
        "/api/bookings", json=booking_payload(event_date="2020-01-01")
    )

    assert response.status_code == 422
    assert "event_date" in response.json()["errors"]


def test_user_sees_only_own_bookings(new_client: Callable[..., TestClient]) -> None:  # type: ignore[name-defined]
    """Заявки других пользователей недоступны."""
    first = new_client()
    register_user(first, login="firstuser", email="first@example.ru")
    first.post("/api/bookings", json=booking_payload())

    second = new_client()
    register_user(second, login="seconduser", email="second@example.ru")

    assert second.get("/api/bookings").json() == []
    assert second.get("/api/bookings/1").status_code == 404


# ---------------------------------------------------------------------------
# Администрирование: фильтры и статусы
# ---------------------------------------------------------------------------


def test_admin_sees_all_bookings_with_applicant(admin_client: TestClient) -> None:
    """Администратор видит заявку вместе с данными заявителя."""
    register_user(admin_client, login="applicant1", email="applicant1@example.ru")
    admin_client.post("/api/bookings", json=booking_payload())
    admin_client.post("/api/auth/logout")
    admin_client.post("/api/auth/login", json=ADMIN_CREDENTIALS)

    response = admin_client.get("/api/admin/bookings")

    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 1
    item = data["items"][0]
    assert item["applicant"]["login"] == "applicant1"
    assert item["status_label"] == "Новая"


def test_admin_filters_bookings_by_status_and_login(admin_client: TestClient) -> None:
    """Фильтрация по статусу и логину заявителя возвращает точную выборку."""
    register_user(admin_client, login="petrov77", email="petrov77@example.ru")
    admin_client.post("/api/bookings", json=booking_payload())
    admin_client.post("/api/auth/logout")
    admin_client.post("/api/auth/login", json=ADMIN_CREDENTIALS)

    by_login = admin_client.get("/api/admin/bookings", params={"login": "petrov"})
    assert by_login.status_code == 200
    assert by_login.json()["meta"]["total"] == 1

    by_status = admin_client.get("/api/admin/bookings", params={"status": "completed"})
    assert by_status.json()["meta"]["total"] == 0

    unknown = admin_client.get("/api/admin/bookings", params={"status": "ghost"})
    assert unknown.status_code == 400


def test_status_lifecycle_and_review_flow(admin_client: TestClient) -> None:
    """Полный сценарий: назначение, завершение и отзыв о мероприятии."""
    register_user(admin_client, login="visitor1", email="visitor1@example.ru")
    created = admin_client.post("/api/bookings", json=booking_payload())
    booking_id = created.json()["id"]
    admin_client.post("/api/auth/logout")
    admin_client.get("/api/bookings")

    # Отзыв невозможен до завершения мероприятия.
    early = admin_client.post(
        f"/api/bookings/{booking_id}/reviews", json={"rating": 5, "comment": "OK"}
    )
    assert early.status_code == 401

    admin_client.post("/api/auth/login", json=ADMIN_CREDENTIALS)
    assigned = admin_client.patch(
        f"/api/admin/bookings/{booking_id}", json={"status": "assigned"}
    )
    assert assigned.status_code == 200
    assert assigned.json()["status_label"] == "Мероприятие назначено"

    # Пользователь не может незаконно изменить статус.
    admin_client.post("/api/auth/logout")
    admin_client.post("/api/auth/login", json={"login": "visitor1", "password": "password123"})
    forbidden = admin_client.patch(
        f"/api/admin/bookings/{booking_id}", json={"status": "completed"}
    )
    assert forbidden.status_code == 403

    # Отзыв доступен только после завершения мероприятия.
    too_early = admin_client.post(
        f"/api/bookings/{booking_id}/reviews", json={"rating": 5, "comment": "Отлично"}
    )
    assert too_early.status_code == 409
    assert "после завершения" in too_early.json()["message"]

    admin_client.post("/api/auth/logout")
    admin_client.post("/api/auth/login", json=ADMIN_CREDENTIALS)
    completed = admin_client.patch(
        f"/api/admin/bookings/{booking_id}", json={"status": "completed"}
    )
    assert completed.status_code == 200

    # Финальный статус закрыт для дальнейших переходов.
    reopened = admin_client.patch(
        f"/api/admin/bookings/{booking_id}", json={"status": "assigned"}
    )
    assert reopened.status_code == 409

    admin_client.post("/api/auth/logout")
    admin_client.post("/api/auth/login", json={"login": "visitor1", "password": "password123"})

    review = admin_client.post(
        f"/api/bookings/{booking_id}/reviews",
        json={"rating": 5, "comment": "Пространство понравилось"},
    )
    assert review.status_code == 201
    assert review.json()["rating"] == 5

    # Повторный отзыв по той же заявке невозможен.
    duplicate = admin_client.post(
        f"/api/bookings/{booking_id}/reviews", json={"rating": 4, "comment": "Ещё раз"}
    )
    assert duplicate.status_code == 409

    bookings = admin_client.get("/api/bookings").json()
    assert bookings[0]["review"]["comment"] == "Пространство понравилось"
    assert bookings[0]["can_review"] is False


def test_review_rating_range_is_validated(user_client: TestClient) -> None:
    """Оценка мероприятия должна быть в диапазоне от 1 до 5."""
    created = user_client.post("/api/bookings", json=booking_payload())
    booking_id = created.json()["id"]

    response = user_client.post(
        f"/api/bookings/{booking_id}/reviews", json={"rating": 9, "comment": ""}
    )

    assert response.status_code == 422
    assert "rating" in response.json()["errors"]


def test_admin_stats_reflect_bookings(admin_client: TestClient) -> None:
    """Статистика панели отражает количество заявок и пользователей."""
    register_user(admin_client, login="guestuser", email="guestuser@example.ru")
    admin_client.post("/api/bookings", json=booking_payload())
    admin_client.post("/api/auth/logout")
    admin_client.post("/api/auth/login", json=ADMIN_CREDENTIALS)

    stats = admin_client.get("/api/admin/stats").json()

    assert stats["total"] == 1
    assert stats["new"] == 1
    assert stats["assigned"] == 0
    assert stats["completed"] == 0
    assert stats["users"] == 1
