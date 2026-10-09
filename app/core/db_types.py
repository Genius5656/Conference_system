"""Пользовательские типы данных SQLAlchemy."""

from __future__ import annotations

from enum import Enum
from typing import Type

from sqlalchemy import Enum as SAEnum


def string_enum(enum_cls: Type[Enum], name: str) -> SAEnum:
    """Создаёт нативное PostgreSQL-перечисление на основе Python-энума.

    В качестве меток типа используются *значения* перечисления
    (например ``new``), а не имена констант — это делает DDL и данные
    в базе единообразными.

    Args:
        enum_cls: Класс перечисления.
        name: Имя типа данных в PostgreSQL.

    Returns:
        Настроенный тип :class:`sqlalchemy.Enum`.
    """
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=True,
        values_callable=lambda items: [item.value for item in items],
    )
