"""HTTP-слой приложения: маршруты и зависимости."""

from fastapi import APIRouter

from app.api.routes import admin, auth, bookings, health, rooms

api_router = APIRouter(prefix="/api")
"""Единый роутер всех API-эндпоинтов."""

api_router.include_router(health.router, tags=["service"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

__all__ = ["api_router"]
