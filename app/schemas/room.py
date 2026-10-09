"""Схемы справочника помещений."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, field_validator


class RoomOut(BaseModel):
    """Помещение в представлении каталога."""

    id: int
    name: str
    kind: str
    kind_label: str
    capacity: int
    description: str
    image_url: str

    model_config = {"from_attributes": True}

    @field_validator("kind", mode="before")
    @classmethod
    def serialize_kind(cls, value: object) -> str:
        """Преобразует перечисление типа помещения в строковое значение."""
        return getattr(value, "value", value)


class RoomBrief(BaseModel):
    """Краткое представление помещения для админ-фильтра."""

    id: Optional[int] = None
    name: str
