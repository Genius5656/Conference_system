"""Модель пользователя портала."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, String, func
from app.core.db_types import string_enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import UserRole

if TYPE_CHECKING:
    from app.models.booking import Booking


class User(Base):
    """Зарегистрированный пользователь портала «Конференции.РФ»."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False, comment="Уникальный логин"
    )
    password_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="Bcrypt-хеш пароля"
    )
    full_name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="ФИО пользователя"
    )
    phone: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Контактный телефон"
    )
    email: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True, comment="Электронная почта"
    )
    role: Mapped[UserRole] = mapped_column(
        string_enum(UserRole, "user_role"),
        nullable=False,
        default=UserRole.USER,
        server_default=UserRole.USER.value,
        comment="Роль в системе",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Дата регистрации",
    )

    bookings: Mapped[List["Booking"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def role_label(self) -> str:
        """Название роли для отображения в интерфейсе."""
        return self.role.label

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User #{self.id} {self.login}>"
