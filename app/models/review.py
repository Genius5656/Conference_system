"""Модель отзыва о проведённом мероприятии."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.booking import Booking


class Review(Base):
    """Отзыв пользователя о качестве проведённого мероприятия."""

    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="Заявка, к которой относится отзыв",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Автор отзыва",
    )
    rating: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Оценка мероприятия (1–5)"
    )
    comment: Mapped[str] = mapped_column(
        Text, nullable=False, default="", comment="Текст отзыва"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Дата публикации отзыва",
    )

    booking: Mapped["Booking"] = relationship(back_populates="review")

    @property
    def short_comment(self) -> str:
        """Обрезанный текст отзыва для карточек."""
        return self.comment[:140]

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Review #{self.id} rating={self.rating}>"
