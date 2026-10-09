"""Служебные маршруты: проверка работоспособности сервиса."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.core.database import get_db

router = APIRouter()


@router.get(
    "/health",
    response_model=Dict[str, str],
    summary="Проверка работоспособности",
)
def health(db: Session = Depends(get_db)) -> Dict[str, str]:
    """Проверяет доступность приложения и базы данных.

    Args:
        db: Сессия базы данных.

    Returns:
        Словарь со статусом сервисов.
    """
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "version": __version__,
        "database": "ok",
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
