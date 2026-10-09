"""Исключения предметной области и обработчики ошибок HTTP."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

DEFAULT_MESSAGES: Dict[str, str] = {
    "missing": "Поле обязательно для заполнения",
    "string_type": "Значение должно быть строкой",
    "string_too_short": "Значение слишком короткое",
    "string_too_long": "Значение слишком длинное",
    "int_parsing": "Введите целое число",
    "int_type": "Значение должно быть числом",
    "date_parsing": "Введите дату в формате ГГГГ-ММ-ДД",
    "time_parsing": "Введите время в формате ЧЧ:ММ",
    "datetime_parsing": "Некорректные дата и время",
    "json_invalid": "Некорректный формат запроса",
    "json_type": "Ожидается объект JSON",
    "model_attributes_type": "Некорректный формат данных",
    "too_short": "Значение слишком короткое",
    "too_long": "Значение слишком длинное",
    "greater_than": "Значение меньше допустимого",
    "less_than": "Значение больше допустимого",
}


class AppError(Exception):
    """Ошибка бизнес-логики, преобразуемая в JSON-ответ с кодом статуса."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        errors: Optional[Dict[str, str]] = None,
        code: str = "invalid_request",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors or {}
        self.code = code

    def to_payload(self) -> Dict[str, Any]:
        """Формирует тело HTTP-ответа."""
        return {
            "code": self.code,
            "message": self.message,
            "errors": self.errors,
        }


def _clean_message(message: str, error_type: str) -> str:
    """Убирает англоязычные префиксы Pydantic из сообщений валидации."""
    for prefix in ("Value error, ", "Assertion failed, "):
        if message.startswith(prefix):
            message = message[len(prefix) :]
    if error_type == "value_error" and message:
        return message
    return DEFAULT_MESSAGES.get(error_type, message or "Некорректное значение")


def _field_name(location: tuple) -> str:
    """Возвращает имя поля из локации ошибки валидации FastAPI."""
    if len(location) >= 2 and location[0] in {"body", "query", "path"}:
        return str(location[1])
    if len(location) == 1:
        return "form"
    return str(location[-1])


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрирует глобальные обработчики ошибок приложения.

    Args:
        app: Экземпляр FastAPI-приложения.
    """

    @app.exception_handler(AppError)
    async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_payload())

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors: Dict[str, str] = {}
        for error in exc.errors():
            field = _field_name(error.get("loc", ()))
            message = _clean_message(str(error.get("msg", "")), error.get("type", ""))
            errors.setdefault(field, message)

        message = (
            "Проверьте правильность заполнения полей"
            if len(errors) > 1
            else next(iter(errors.values()))
        )
        return JSONResponse(
            status_code=422,
            content={
                "code": "validation_error",
                "message": message,
                "errors": errors,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "Ошибка запроса"
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": "http_error",
                "message": detail,
                "errors": {},
            },
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "code": "internal_error",
                "message": "Внутренняя ошибка сервера. Повторите попытку позже.",
                "errors": {},
            },
        )
