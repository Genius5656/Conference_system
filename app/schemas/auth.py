"""Схемы регистрации и авторизации пользователей."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Dict

from pydantic import BaseModel, field_validator

LOGIN_PATTERN = re.compile(r"^[A-Za-z0-9]{6,32}$")
FULL_NAME_PATTERN = re.compile(r"^[А-Яа-яЁё]+(?:[ ]+[А-Яа-яЁё]+)*$")
PHONE_PATTERN = re.compile(r"^8\(\d{3}\)\d{3}-\d{2}-\d{2}$")
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

LOGIN_MESSAGE = (
    "Логин должен содержать только латинские буквы и цифры "
    "и быть не короче 6 символов"
)
PASSWORD_MESSAGE = "Пароль должен содержать от 8 до 72 символов"
FULL_NAME_MESSAGE = "ФИО может содержать только символы кириллицы и пробелы"
PHONE_MESSAGE = "Телефон должен соответствовать формату 8(XXX)XXX-XX-XX"
EMAIL_MESSAGE = "Введите корректный адрес электронной почты"


class UserCreate(BaseModel):
    """Данные для создания пользователя на странице регистрации."""

    login: str
    password: str
    full_name: str
    phone: str
    email: str

    @field_validator("login")
    @classmethod
    def validate_login(cls, value: str) -> str:
        value = value.strip()
        if not LOGIN_PATTERN.match(value):
            raise ValueError(LOGIN_MESSAGE)
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not 8 <= len(value) <= 72:
            raise ValueError(PASSWORD_MESSAGE)
        return value

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not FULL_NAME_PATTERN.match(value):
            raise ValueError(FULL_NAME_MESSAGE)
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()
        if not PHONE_PATTERN.match(value):
            raise ValueError(PHONE_MESSAGE)
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip()
        if not EMAIL_PATTERN.match(value) or len(value) > 128:
            raise ValueError(EMAIL_MESSAGE)
        return value.lower()


class UserLogin(BaseModel):
    """Данные для входа на странице авторизации."""

    login: str
    password: str

    @field_validator("login")
    @classmethod
    def validate_login(cls, value: str) -> str:
        return value.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value:
            raise ValueError("Введите пароль")
        return value


class UserOut(BaseModel):
    """Публичное представление пользователя."""

    id: int
    login: str
    full_name: str
    phone: str
    email: str
    role: str
    role_label: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("role", mode="before")
    @classmethod
    def serialize_role(cls, value: object) -> str:
        """Преобразует перечисление роли в строковое значение."""
        return getattr(value, "value", value)


def validation_errors(**messages: str) -> Dict[str, str]:
    """Формирует словарь ошибок валидации для ответа API.

    Args:
        **messages: Пары ``поле=сообщение``.

    Returns:
        Словарь вида ``{"поле": "сообщение"}``.
    """
    return {field: message for field, message in messages.items()}
