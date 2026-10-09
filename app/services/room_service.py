"""Работа со справочником помещений."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Room


def list_rooms(db: Session) -> List[Room]:
    """Возвращает все помещения портала, отсортированные по названию.

    Args:
        db: Сессия базы данных.

    Returns:
        Список помещений.
    """
    return list(db.scalars(select(Room).order_by(Room.name)).all())


def get_room(db: Session, room_id: int) -> Optional[Room]:
    """Возвращает помещение по идентификатору.

    Args:
        db: Сессия базы данных.
        room_id: Идентификатор помещения.

    Returns:
        Помещение или ``None``, если запись не найдена.
    """
    return db.get(Room, room_id)
