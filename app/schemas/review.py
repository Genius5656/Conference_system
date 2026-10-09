"""Схемы отзывов о проведённых мероприятиях."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

MAX_REVIEW_LENGTH = 1000
RATING_MESSAGE = "Оценка должна быть от 1 до 5"


class ReviewOut(BaseModel):
    """Отзыв, прикреплённый к заявке."""

    id: int
    rating: int
    comment: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewCreate(BaseModel):
    """Данные формы отзыва о мероприятии."""

    rating: int
    comment: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, value: int) -> int:
        if not 1 <= value <= 5:
            raise ValueError(RATING_MESSAGE)
        return value

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, value: Optional[str]) -> str:
        comment = (value or "").strip()
        if len(comment) > MAX_REVIEW_LENGTH:
            raise ValueError(f"Отзыв не должен превышать {MAX_REVIEW_LENGTH} символов")
        return comment
