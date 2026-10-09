"""Публикация отзывов о проведённых мероприятиях."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.enums import BookingStatus
from app.core.exceptions import AppError
from app.models import Booking, Review, User
from app.schemas.review import ReviewCreate

REVIEW_NOT_AVAILABLE_MESSAGE = (
    "Отзыв можно оставить только после завершения мероприятия"
)
REVIEW_EXISTS_MESSAGE = "Отзыв по этой заявке уже оставлен"
BOOKING_FORBIDDEN_MESSAGE = "Заявка принадлежит другому пользователю"


def create_review(
    db: Session, user: User, booking: Booking, payload: ReviewCreate
) -> Review:
    """Создаёт отзыв о мероприятии по завершённой заявке.

    Args:
        db: Сессия базы данных.
        user: Автор отзыва.
        booking: Заявка, для которой создаётся отзыв.
        payload: Валидированные данные отзыва.

    Returns:
        Созданный отзыв.

    Raises:
        AppError: Если заявка не принадлежит пользователю (403),
            мероприятие ещё не завершено (409) или отзыв уже есть (409).
    """
    if booking.user_id != user.id:
        raise AppError(
            BOOKING_FORBIDDEN_MESSAGE,
            status_code=403,
            code="forbidden",
        )

    if booking.status is not BookingStatus.COMPLETED:
        raise AppError(
            REVIEW_NOT_AVAILABLE_MESSAGE,
            status_code=409,
            errors={"rating": REVIEW_NOT_AVAILABLE_MESSAGE},
            code="review_not_available",
        )

    if booking.review is not None:
        raise AppError(
            REVIEW_EXISTS_MESSAGE,
            status_code=409,
            errors={"rating": REVIEW_EXISTS_MESSAGE},
            code="review_exists",
        )

    review = Review(
        booking_id=booking.id,
        user_id=user.id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    db.flush()
    db.refresh(review)
    return review
