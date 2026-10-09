"""Перечисления предметной области и их человекочитаемые представления."""

from __future__ import annotations

import enum


class StringEnum(str, enum.Enum):
    """База для перечислений, сериализуемых в обычную строку."""

    def __str__(self) -> str:  # noqa: D105
        return self.value


class UserRole(StringEnum):
    """Роль пользователя портала."""

    USER = "user"
    ADMIN = "admin"

    @property
    def label(self) -> str:
        """Название роли для интерфейса."""
        return {
            UserRole.USER: "Пользователь",
            UserRole.ADMIN: "Администратор",
        }[self]


class RoomKind(StringEnum):
    """Тип помещения для конференции."""

    AUDITORIUM = "auditorium"
    COWORKING = "coworking"
    CINEMA = "cinema"

    @property
    def label(self) -> str:
        """Название типа помещения для интерфейса."""
        return {
            RoomKind.AUDITORIUM: "Аудитория",
            RoomKind.COWORKING: "Коворкинг",
            RoomKind.CINEMA: "Кинозал",
        }[self]


class PaymentMethod(StringEnum):
    """Способ оплаты заявки."""

    ONSITE = "onsite"
    SBP = "sbp"

    @property
    def label(self) -> str:
        """Название способа оплаты для интерфейса."""
        return {
            PaymentMethod.ONSITE: "При очном посещении",
            PaymentMethod.SBP: "Перевод по системе СБП",
        }[self]


class BookingStatus(StringEnum):
    """Статус заявки на бронирование помещения."""

    NEW = "new"
    ASSIGNED = "assigned"
    COMPLETED = "completed"

    @property
    def label(self) -> str:
        """Название статуса для интерфейса."""
        return {
            BookingStatus.NEW: "Новая",
            BookingStatus.ASSIGNED: "Мероприятие назначено",
            BookingStatus.COMPLETED: "Завершено",
        }[self]


ALLOWED_STATUS_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.NEW: {BookingStatus.ASSIGNED, BookingStatus.COMPLETED},
    BookingStatus.ASSIGNED: {BookingStatus.COMPLETED, BookingStatus.NEW},
    BookingStatus.COMPLETED: set(),
}
"""Допустимые переходы между статусами заявки."""

STATUS_FILTERS: dict[str, BookingStatus | None] = {
    "all": None,
    "new": BookingStatus.NEW,
    "assigned": BookingStatus.ASSIGNED,
    "completed": BookingStatus.COMPLETED,
}
"""Маппинг значений фильтра из админ-панели на статусы."""
