"""Модель заявки на бронирование помещения."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, Time, func
from app.core.db_types import string_enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import BookingStatus, PaymentMethod

if TYPE_CHECKING:
    from app.models.review import Review
    from app.models.room import Room
    from app.models.user import User


class Booking(Base):
    """Заявка пользователя на проведение конференции в помещении."""

    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint(
            "(room_id IS NOT NULL) OR (room_name IS NOT NULL)",
            name="ck_bookings_room_source",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Заявитель",
    )
    room_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("rooms.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        comment="Помещение из справочника",
    )
    room_name: Mapped[Optional[str]] = mapped_column(
        String(120), nullable=True, comment="Название помещения вне справочника"
    )
    event_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="Дата начала конференции"
    )
    start_time: Mapped[Optional[time]] = mapped_column(
        Time, nullable=True, comment="Предпочтительное время начала"
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(
        string_enum(PaymentMethod, "payment_method"),
        nullable=False,
        comment="Способ оплаты",
    )
    status: Mapped[BookingStatus] = mapped_column(
        string_enum(BookingStatus, "booking_status"),
        nullable=False,
        default=BookingStatus.NEW,
        server_default=BookingStatus.NEW.value,
        index=True,
        comment="Статус заявки",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Дата подачи заявки",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Дата последнего изменения",
    )

    user: Mapped["User"] = relationship(back_populates="bookings")
    room: Mapped[Optional["Room"]] = relationship(back_populates="bookings")
    review: Mapped[Optional["Review"]] = relationship(
        back_populates="booking",
        cascade="all, delete-orphan",
        uselist=False,
    )

    @property
    def display_room_name(self) -> str:
        """Название незарегистрированного помещения, если оно было указано."""
        return self.room_name or ""

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Booking #{self.id} status={self.status.value}>"
