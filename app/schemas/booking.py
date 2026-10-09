"""Схемы заявок на бронирование помещений."""

from __future__ import annotations

import re
from datetime import date, datetime, time
from typing import List, Optional

from pydantic import BaseModel, field_validator

from app.core.enums import BookingStatus, PaymentMethod
from app.schemas.review import ReviewOut

ROOM_NAME_PATTERN = re.compile(r"^[A-Za-zА-Яа-яЁё0-9\s\-«»\"'(),.]{2,120}$")
ROOM_NAME_MESSAGE = (
    "Укажите название помещения: буквы, цифры, пробелы и знаки препинания"
)
DATE_MESSAGE = "Дата начала конференции не может быть в прошлом"
PAYMENT_MESSAGE = "Выберите способ оплаты из списка"


class BookingCreate(BaseModel):
    """Данные формы формирования заявки."""

    room_id: Optional[int] = None
    room_name: Optional[str] = None
    event_date: date
    start_time: Optional[time] = None
    payment_method: str

    @field_validator("room_name")
    @classmethod
    def validate_room_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = " ".join(value.split())
        if not value:
            return None
        if not ROOM_NAME_PATTERN.match(value):
            raise ValueError(ROOM_NAME_MESSAGE)
        return value

    @field_validator("event_date")
    @classmethod
    def validate_event_date(cls, value: date) -> date:
        if value < date.today():
            raise ValueError(DATE_MESSAGE)
        return value

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, value: str) -> str:
        if value not in {method.value for method in PaymentMethod}:
            raise ValueError(PAYMENT_MESSAGE)
        return value


class BookingOut(BaseModel):
    """Заявка в представлении личного кабинета пользователя."""

    id: int
    room_id: Optional[int]
    room_name: str
    room_kind: Optional[str] = None
    room_kind_label: Optional[str] = None
    event_date: date
    start_time: Optional[time]
    payment_method: str
    payment_method_label: str
    status: str
    status_label: str
    created_at: datetime
    can_review: bool = False
    review: Optional[ReviewOut] = None

    @field_validator("status", "payment_method", "room_kind", mode="before")
    @classmethod
    def serialize_enum(cls, value: object) -> object:
        """Преобразует перечисления в их строковые значения."""
        return getattr(value, "value", value)


class AdminBookingOut(BookingOut):
    """Заявка в представлении панели администратора."""

    applicant: dict


class BookingStatusUpdate(BaseModel):
    """Изменение статуса заявки администратором."""

    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in {status.value for status in BookingStatus}:
            raise ValueError("Некорректный статус заявки")
        return value


class PageMeta(BaseModel):
    """Метаданные постраничной выборки."""

    total: int
    page: int
    page_size: int

    @property
    def pages(self) -> int:
        """Количество страниц выборки."""
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


class BookingPage(BaseModel):
    """Страница списка заявок."""

    items: List[AdminBookingOut]
    meta: PageMeta


def build_booking_out(booking, review=None) -> BookingOut:
    """Собирает DTO заявки из ORM-объекта.

    Args:
        booking: ORM-объект заявки с подгруженными ``room`` и ``user``.
        review: Отзыв, если он уже оставлен.

    Returns:
        DTO заявки для ответа API.
    """
    room = booking.room
    return BookingOut(
        id=booking.id,
        room_id=booking.room_id,
        room_name=room.name if room else booking.display_room_name,
        room_kind=room.kind.value if room else None,
        room_kind_label=room.kind_label if room else None,
        event_date=booking.event_date,
        start_time=booking.start_time,
        payment_method=booking.payment_method.value,
        payment_method_label=booking.payment_method.label,
        status=booking.status.value,
        status_label=booking.status.label,
        created_at=booking.created_at,
        can_review=(
            booking.status is BookingStatus.COMPLETED and review is None
        ),
        review=ReviewOut.model_validate(review) if review else None,
    )


def build_admin_booking_out(booking) -> AdminBookingOut:
    """Собирает DTO заявки для панели администратора.

    Args:
        booking: ORM-объект заявки с подгруженными ``room``, ``user`` и ``review``.

    Returns:
        DTO заявки с данными заявителя.
    """
    base = build_booking_out(booking, booking.review)
    applicant = booking.user
    payload = base.model_dump()
    payload["applicant"] = {
        "id": applicant.id,
        "login": applicant.login,
        "full_name": applicant.full_name,
        "phone": applicant.phone,
        "email": applicant.email,
    }
    return AdminBookingOut(**payload)
