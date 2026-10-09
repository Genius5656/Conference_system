"""Маршруты заявок и отзывов авторизованного пользователя."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.booking import BookingCreate, BookingOut, build_booking_out
from app.schemas.review import ReviewCreate, ReviewOut
from app.services import booking_service, review_service

router = APIRouter()


@router.get(
    "",
    response_model=List[BookingOut],
    summary="Мои заявки",
)
def list_my_bookings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[BookingOut]:
    """Возвращает заявки текущего пользователя с отзывами.

    Args:
        user: Текущий пользователь.
        db: Сессия базы данных.

    Returns:
        Список заявок пользователя.
    """
    bookings = booking_service.list_user_bookings(db, user)
    return [build_booking_out(booking, booking.review) for booking in bookings]


@router.post(
    "",
    response_model=BookingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создание заявки на бронирование",
)
def create_booking(
    payload: BookingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BookingOut:
    """Принимает заявку пользователя и направляет её администратору.

    Args:
        payload: Данные формы формирования заявки.
        user: Текущий пользователь.
        db: Сессия базы данных.

    Returns:
        Созданная заявка со статусом «Новая».
    """
    booking = booking_service.create_booking(db, user, payload)
    return build_booking_out(booking, booking.review)


@router.get(
    "/{booking_id}",
    response_model=BookingOut,
    summary="Детали заявки",
)
def get_booking(
    booking_id: int = Path(..., ge=1, description="Идентификатор заявки"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BookingOut:
    """Возвращает детали заявки текущего пользователя.

    Args:
        booking_id: Идентификатор заявки.
        user: Текущий пользователь.
        db: Сессия базы данных.

    Returns:
        Заявка с текущим статусом и отзывом.
    """
    booking = booking_service.get_booking_for_user(db, booking_id, user)
    return build_booking_out(booking, booking.review)


@router.post(
    "/{booking_id}/reviews",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
    summary="Отзыв о проведённом мероприятии",
)
def create_review(
    payload: ReviewCreate,
    booking_id: int = Path(..., ge=1, description="Идентификатор заявки"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReviewOut:
    """Создаёт отзыв по завершённой заявке.

    Args:
        payload: Оценка и текст отзыва.
        booking_id: Идентификатор заявки.
        user: Текущий пользователь.
        db: Сессия базы данных.

    Returns:
        Созданный отзыв.
    """
    booking = booking_service.get_booking_for_user(db, booking_id, user)
    review = review_service.create_review(db, user, booking, payload)
    return ReviewOut.model_validate(review)
