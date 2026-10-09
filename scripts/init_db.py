"""Создание схемы базы данных и наполнение стартовыми данными.

Скрипт выполняет ровно те же действия, что и автоматическая инициализация
при старте приложения, но позволяет выполнить её вручную:

    python scripts/init_db.py

Полезно при первом запуске, развёртывании или восстановлении базы данных.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.config import get_settings  # noqa: E402
from app.core.database import engine  # noqa: E402
from app.db import bootstrap_database  # noqa: E402


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Разбирает аргументы командной строки.

    Args:
        argv: Аргументы запуска скрипта.

    Returns:
        Разобранные аргументы.
    """
    parser = argparse.ArgumentParser(
        description="Инициализация БД портала «Конференции.РФ»"
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Переопределяет DATABASE_URL (по умолчанию берётся из .env)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Показать подключение к БД без выполнения инициализации",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """Точка входа скрипта.

    Args:
        argv: Аргументы командной строки.

    Returns:
        Код завершения процесса.
    """
    args = parse_args(argv)
    settings = get_settings()
    target = args.url or settings.database_url

    print("База данных:", target.split("@")[-1])

    if args.dry_run:
        print("Режим dry-run: инициализация не выполнялась.")
        return 0

    bootstrap_database(engine)

    print("Схема создана.")
    print("Стартовые помещения добавлены (5 шт.).")
    print(f"Администратор подготовлен: {settings.admin_login}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
