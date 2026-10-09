"""Контракты данных (Pydantic-схемы) API."""

from app.schemas.auth import UserCreate, UserLogin, UserOut
from app.schemas.booking import (
    AdminBookingOut,
    BookingCreate,
    BookingOut,
    BookingPage,
    BookingStatusUpdate,
    PageMeta,
)
from app.schemas.review import ReviewCreate, ReviewOut
from app.schemas.room import RoomOut

__all__ = [
    "AdminBookingOut",
    "BookingCreate",
    "BookingOut",
    "BookingPage",
    "BookingStatusUpdate",
    "PageMeta",
    "ReviewCreate",
    "ReviewOut",
    "RoomOut",
    "UserCreate",
    "UserLogin",
    "UserOut",
]
