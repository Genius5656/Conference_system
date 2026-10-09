"""Бизнес-логика заявок на бронирование помещений."""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import (
    ALLOWED_STATUS_TRANSITIONS,
    BookingStatus,
    PaymentMethod,
    UserRole,
)
from app.core.exceptions import AppError
from app.models import Booking, Review, Room, User
from app.schemas.booking import BookingCreate
from app.services.room_service import get_room

ROOM_REQUIRED_MESSAGE = "Выберите помещение из списка или введите его название"
ROOM_NOT_FOUND_MESSAGE = "Выбранное помещение не найдено в справочнике"
FORBIDDEN_STATUS_MESSAGE = "Недопустимая смена статуса заявки"
BOOKING_NOT_FOUND_MESSAGE = "Заявка не найдена"


def create_booking(
    db: Session, user: User, payload: BookingCreate
) -> Booking:
    """Создаёт заявку на бронирование помещения.

    Args:
        db: Сессия базы данных.
        user: Автор заявки.
        payload: Валидированные данные формы заявки.

    Returns:
        Созданная заявка со статусом «Новая».

    Raises:
        AppError: Если не указано помещение или оно отсутствует в справочнике.
    """
    room: Optional[Room] = None
    if payload.room_id is not None:
        room = get_room(db, payload.room_id)
        if room is None:
            raise AppError(
                ROOM_NOT_FOUND_MESSAGE,
                status_code=400,
                errors={"room_id": ROOM_NOT_FOUND_MESSAGE},
                code="room_not_found",
            )

    if room is None and not payload.room_name:
        raise AppError(
            ROOM_REQUIRED_MESSAGE,
            status_code=400,
            errors={"room_id": ROOM_REQUIRED_MESSAGE},
            code="room_required",
        )

    booking = Booking(
        user_id=user.id,
        room_id=room.id if room else None,
        room_name=None if room else payload.room_name,
        event_date=payload.event_date,
        start_time=payload.start_time,
        payment_method=PaymentMethod(payload.payment_method),
        status=BookingStatus.NEW,
    )
    db.add(booking)
    db.flush()
    return _load_booking(db, booking.id)


def list_user_bookings(db: Session, user: User) -> List[Booking]:
    """Возвращает заявки пользователя вместе с отзывами.

    Args:
        db: Сессия базы данных.
        user: Владелец заявок.

    Returns:
        Список заявок, отсортированный от новых к старым.
    """
    statement = (
        select(Booking)
        .where(Booking.user_id == user.id)
        .options(
            selectinload(Booking.room),
            selectinload(Booking.review),
        )
        .order_by(Booking.created_at.desc(), Booking.id.desc())
    )
    return list(db.scalars(statement).all())


def get_booking_for_user(
    db: Session, booking_id: int, user: User
) -> Booking:
    """Возвращает заявку, принадлежащую пользователю.

    Args:
        db: Сессия базы данных.
        booking_id: Идентификатор заявки.
        user: Пользователь, запрашивающий заявку.

    Returns:
        Заявка с подгруженными связями.

    Raises:
        AppError: Если заявка не найдена или принадлежит другому пользователю.
    """
    booking = _load_booking(db, booking_id)
    if booking is None or booking.user_id != user.id:
        raise AppError(
            BOOKING_NOT_FOUND_MESSAGE,
            status_code=404,
            code="not_found",
        )
    return booking


def admin_list_bookings(
    db: Session,
    *,
    status: Optional[BookingStatus] = None,
    login: Optional[str] = None,
    room: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = 1,
    page_size: int = 12,
) -> Tuple[List[Booking], int]:
    """Формирует отфильтрованную и отсортированную выборку заявок.

    Args:
        db: Сессия базы данных.
        status: Фильтр по статусу заявки.
        login: Фильтр по части логина заявителя.
        room: Фильтр по части названия помещения.
        date_from: Нижняя граница даты конференции.
        date_to: Верхняя граница даты конференции.
        page: Номер страницы (с единицы).
        page_size: Размер страницы.

    Returns:
        Кортеж из списка заявок и общего числа записей.
    """
    criteria = []
    if status is not None:
        criteria.append(Booking.status == status)
    if login:
        criteria.append(
            Booking.user.has(User.login.ilike(f"%{login.strip()}%"))
        )
    if room:
        needle = f"%{room.strip()}%"
        criteria.append(
            or_(
                Booking.room.has(Room.name.ilike(needle)),
                Booking.room_name.ilike(needle),
            )
        )
    if date_from is not None:
        criteria.append(Booking.event_date >= date_from)
    if date_to is not None:
        criteria.append(Booking.event_date <= date_to)

    total = db.scalar(
        select(func.count()).select_from(Booking).where(*criteria)
    ) or 0

    statement = (
        select(Booking)
        .where(*criteria)
        .options(
            selectinload(Booking.room),
            selectinload(Booking.user),
            selectinload(Booking.review),
        )
        .order_by(Booking.created_at.desc(), Booking.id.desc())
        .offset(max(page - 1, 0) * page_size)
        .limit(page_size)
    )
    return list(db.scalars(statement).all()), int(total)


def admin_get_booking(db: Session, booking_id: int) -> Booking:
    """Возвращает заявку для панели администратора.

    Args:
        db: Сессия базы данных.
        booking_id: Идентификатор заявки.

    Returns:
        Заявка с подгруженными связями.

    Raises:
        AppError: Если заявка не найдена.
    """
    booking = _load_booking(db, booking_id)
    if booking is None:
        raise AppError(
            BOOKING_NOT_FOUND_MESSAGE,
            status_code=404,
            code="not_found",
        )
    return booking


def update_booking_status(
    db: Session, booking_id: int, new_status: BookingStatus
) -> Booking:
    """Меняет статус заявки с учётом правил перехода.

    Args:
        db: Сессия базы данных.
        booking_id: Идентификатор заявки.
        new_status: Новый статус заявки.

    Returns:
        Обновлённая заявка.

    Raises:
        AppError: Если заявка не найдена (404) или переход запрещён (409).
    """
    booking = admin_get_booking(db, booking_id)

    if new_status is booking.status:
        return booking

    allowed = ALLOWED_STATUS_TRANSITIONS[booking.status]
    if new_status not in allowed:
        allowed_labels = ", ".join(
            sorted(status.label for status in allowed)
        ) or "нет (финальный статус)"
        raise AppError(
            f"{FORBIDDEN_STATUS_MESSAGE}. Допустимые варианты: {allowed_labels}",
            status_code=409,
            errors={"status": FORBIDDEN_STATUS_MESSAGE},
            code="invalid_status_transition",
        )

    booking.status = new_status
    db.flush()
    return _load_booking(db, booking.id)


def get_stats(db: Session) -> Dict[str, int]:
    """Собирает сводную статистику для панели администратора.

    Args:
        db: Сессия базы данных.

    Returns:
        Словарь счётчиков по заявкам, пользователям и отзывам.
    """
    status_rows = db.execute(
        select(Booking.status, func.count(Booking.id)).group_by(Booking.status)
    ).all()
    counts = {status.value: 0 for status in BookingStatus}
    total = 0
    for status, count in status_rows:
        counts[status.value] = int(count)
        total += int(count)

    users_count = int(
        db.scalar(select(func.count(User.id)).where(User.role == UserRole.USER))
        or 0
    )
    reviews_count = int(db.scalar(select(func.count(Review.id))) or 0)

    return {
        "total": total,
        "new": counts[BookingStatus.NEW.value],
        "assigned": counts[BookingStatus.ASSIGNED.value],
        "completed": counts[BookingStatus.COMPLETED.value],
        "users": users_count,
        "reviews": reviews_count,
    }


def _load_booking(db: Session, booking_id: int) -> Optional[Booking]:
    """Подгружает заявку со всеми связями."""
    statement = (
        select(Booking)
        .where(Booking.id == booking_id)
        .options(
            selectinload(Booking.room),
            selectinload(Booking.user),
            selectinload(Booking.review),
        )
    )
    return db.scalar(statement)
