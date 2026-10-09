"""Модель помещения, доступного для бронирования."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import Integer, String, Text
from app.core.db_types import string_enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import RoomKind

if TYPE_CHECKING:
    from app.models.booking import Booking


class Room(Base):
    """Помещение для проведения конференции: аудитория, коворкинг, кинозал."""

    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False, comment="Название помещения"
    )
    kind: Mapped[RoomKind] = mapped_column(
        string_enum(RoomKind, "room_kind"),
        nullable=False,
        comment="Тип помещения",
    )
    capacity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="Вместимость, чел."
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False, default="", comment="Описание помещения"
    )
    image_url: Mapped[str] = mapped_column(
        String(255), nullable=False, default="", comment="Изображение помещения"
    )

    bookings: Mapped[List["Booking"]] = relationship(back_populates="room")

    @property
    def kind_label(self) -> str:
        """Название типа помещения для отображения в интерфейсе."""
        return self.kind.label

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Room #{self.id} {self.name}>"
