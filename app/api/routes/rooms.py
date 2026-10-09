"""Маршруты справочника помещений."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.room import RoomOut
from app.services import room_service

router = APIRouter()


@router.get(
    "",
    response_model=List[RoomOut],
    summary="Список помещений для конференций",
)
def list_rooms(db: Session = Depends(get_db)) -> List[RoomOut]:
    """Возвращает каталог помещений портала.

    Args:
        db: Сессия базы данных.

    Returns:
        Список помещений.
    """
    return [RoomOut.model_validate(room) for room in room_service.list_rooms(db)]
