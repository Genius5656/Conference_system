"""Маршруты панели администратора портала."""

from __future__ import annotations

from datetime import date
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.core.enums import STATUS_FILTERS, BookingStatus
from app.core.exceptions import AppError
from app.schemas.booking import (
    AdminBookingOut,
    BookingPage,
    BookingStatusUpdate,
    PageMeta,
    build_admin_booking_out,
)
from app.services import booking_service

router = APIRouter(dependencies=[Depends(require_admin)])

INVALID_STATUS_FILTER_MESSAGE = "Некорректный фильтр статуса заявки"
INVALID_DATE_RANGE_MESSAGE = "Дата «от» не может быть позже даты «до»"

PAGE_SIZE_DEFAULT = 12


@router.get(
    "/bookings",
    response_model=BookingPage,
    summary="Все заявки пользователей с фильтрацией",
)
def list_bookings(
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(
        default=None,
        alias="status",
        description="Фильтр по статусу: all | new | assigned | completed",
    ),
    login: Optional[str] = Query(
        default=None, max_length=32, description="Часть логина заявителя"
    ),
    room: Optional[str] = Query(
        default=None, max_length=120, description="Часть названия помещения"
    ),
    date_from: Optional[date] = Query(
        default=None, description="Дата конференции от (ГГГГ-ММ-ДД)"
    ),
    date_to: Optional[date] = Query(
        default=None, description="Дата конференции до (ГГГГ-ММ-ДД)"
    ),
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    page_size: int = Query(
        default=PAGE_SIZE_DEFAULT, ge=1, le=100, description="Размер страницы"
    ),
) -> BookingPage:
    """Возвращает заявки пользователей с учётом фильтров.

    Args:
        db: Сессия базы данных.
        status_filter: Значение фильтра статуса.
        login: Часть логина заявителя.
        room: Часть названия помещения.
        date_from: Нижняя граница даты конференции.
        date_to: Верхняя граница даты конференции.
        page: Номер страницы.
        page_size: Размер страницы.

    Returns:
        Страница заявок с метаданными выборки.

    Raises:
        AppError: 400 — задан некорректный фильтр или диапазон дат.
    """
    key = (status_filter or "all").lower()
    if key not in STATUS_FILTERS:
        raise AppError(
            INVALID_STATUS_FILTER_MESSAGE,
            status_code=400,
            errors={"status": INVALID_STATUS_FILTER_MESSAGE},
            code="invalid_filter",
        )

    if date_from and date_to and date_from > date_to:
        raise AppError(
            INVALID_DATE_RANGE_MESSAGE,
            status_code=400,
            errors={"date_from": INVALID_DATE_RANGE_MESSAGE},
            code="invalid_date_range",
        )

    items, total = booking_service.admin_list_bookings(
        db,
        status=STATUS_FILTERS[key],
        login=login,
        room=room,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return BookingPage(
        items=[build_admin_booking_out(booking) for booking in items],
        meta=PageMeta(total=total, page=page, page_size=page_size),
    )


@router.patch(
    "/bookings/{booking_id}",
    response_model=AdminBookingOut,
    summary="Смена статуса заявки",
)
def update_booking_status(
    payload: BookingStatusUpdate,
    booking_id: int = Path(..., ge=1, description="Идентификатор заявки"),
    db: Session = Depends(get_db),
) -> AdminBookingOut:
    """Меняет статус заявки в соответствии с правилами перехода.

    Args:
        payload: Новый статус заявки.
        booking_id: Идентификатор заявки.
        db: Сессия базы данных.

    Returns:
        Обновлённая заявка.

    Raises:
        AppError: 404 — заявка не найдена; 409 — переход запрещён.
    """
    booking = booking_service.update_booking_status(
        db, booking_id, BookingStatus(payload.status)
    )
    return build_admin_booking_out(booking)


@router.get(
    "/stats",
    response_model=Dict[str, int],
    summary="Сводная статистика портала",
)
def get_stats(db: Session = Depends(get_db)) -> Dict[str, int]:
    """Возвращает счётчики для главной панели администратора.

    Args:
        db: Сессия базы данных.

    Returns:
        Словарь со счётчиками заявок, пользователей и отзывов.
    """
    return booking_service.get_stats(db)


@router.get(
    "/bookings/{booking_id}",
    response_model=AdminBookingOut,
    summary="Детали заявки для администратора",
)
def get_booking(
    booking_id: int = Path(..., ge=1, description="Идентификатор заявки"),
    db: Session = Depends(get_db),
) -> AdminBookingOut:
    """Возвращает детали заявки.

    Args:
        booking_id: Идентификатор заявки.
        db: Сессия базы данных.

    Returns:
        Заявка с данными заявителя.
    """
    booking = booking_service.admin_get_booking(db, booking_id)
    return build_admin_booking_out(booking)
