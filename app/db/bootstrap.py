"""Инициализация схемы базы данных и наполнение стартовыми данными."""

from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine as default_engine
from app.core.enums import RoomKind, UserRole
from app.core.security import hash_password, verify_password
from app.models import Room, User

SEED_ROOMS: List[Tuple[str, RoomKind, int, str, str]] = [
    (
        "Аудитория №1",
        RoomKind.AUDITORIUM,
        60,
        "Светлая аудитория с проектором, экраном и мягкой мебелью — "
        "подходит для секционных докладов и воркшопов.",
        "/assets/img/room-auditorium-1.webp",
    ),
    (
        "Лекционный зал",
        RoomKind.AUDITORIUM,
        120,
        "Просторный зал с двумя экранами и рядом кресел для пленарных "
        "заседаний и больших презентаций.",
        "/assets/img/room-auditorium-2.webp",
    ),
    (
        "Коворкинг «Простор»",
        RoomKind.COWORKING,
        40,
        "Открытое пространство с круглыми столами, зонами тишины и "
        "кухней для неформального общения участников.",
        "/assets/img/room-coworking-1.webp",
    ),
    (
        "Коворкинг «Минимал»",
        RoomKind.COWORKING,
        25,
        "Компактная площадка для рабочих групп, митапов и небольших "
        "семинаров в неформатной атмосфере.",
        "/assets/img/room-coworking-2.webp",
    ),
    (
        "Кинозал «Премьера»",
        RoomKind.CINEMA,
        150,
        "Зал с киногоризонтом, профессиональным звуком и амфитеатром "
        "для показов, кейсов и пленарных сессий.",
        "/assets/img/room-cinema.webp",
    ),
]
"""Стартовый справочник помещений портала."""


def create_schema(engine: Engine) -> None:
    """Создаёт таблицы схемы приложения (идемпотентно).

    Args:
        engine: Engine подключения к базе данных.
    """
    Base.metadata.create_all(bind=engine, checkfirst=True)


def seed_rooms(db: Session) -> int:
    """Добавляет помещения из справочника, если их ещё нет.

    Args:
        db: Сессия базы данных.

    Returns:
        Количество созданных помещений.
    """
    existing = set(db.scalars(select(Room.name)).all())
    created = 0
    for name, kind, capacity, description, image_url in SEED_ROOMS:
        if name in existing:
            continue
        db.add(
            Room(
                name=name,
                kind=kind,
                capacity=capacity,
                description=description,
                image_url=image_url,
            )
        )
        created += 1
    db.flush()
    return created


def seed_admin(db: Session) -> bool:
    """Создаёт учётную запись администратора портала.

    Учётные данные берутся из настроек ``ADMIN_LOGIN`` / ``ADMIN_PASSWORD``
    (по умолчанию Conf2027 / Demo77, согласно заданию).

    Args:
        db: Сессия базы данных.

    Returns:
        ``True``, если учётная запись была создана или обновлена.
    """
    settings = get_settings()
    admin = db.scalar(select(User).where(User.login == settings.admin_login))

    if admin is None:
        db.add(
            User(
                login=settings.admin_login,
                password_hash=hash_password(settings.admin_password),
                full_name="Администратор портала",
                phone="8(000)000-00-00",
                email="admin@conference-rf.ru",
                role=UserRole.ADMIN,
            )
        )
        db.flush()
        return True

    if not verify_password(settings.admin_password, admin.password_hash):
        admin.password_hash = hash_password(settings.admin_password)
        db.flush()
        return True

    return False


def bootstrap_database(engine: Optional[Engine] = None) -> None:
    """Выполняет полную инициализацию базы данных приложения.

    Args:
        engine: Engine подключения. По умолчанию — глобальный engine приложения.
    """
    target_engine = engine or default_engine
    create_schema(target_engine)

    with SessionLocal() as db:
        try:
            seed_rooms(db)
            seed_admin(db)
            db.commit()
        except Exception:
            db.rollback()
            raise
