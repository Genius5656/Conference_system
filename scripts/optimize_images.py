"""Оптимизация исходных изображений для веб-интерфейса.

Скрипт берёт «сырые» изображения из предоставленного каталога `media`,
упрощает их до веб-формата (WebP) и сохраняет в каталог статических
файлов приложения. Повторный запуск безопасен — файлы перезаписываются.

Пример запуска из корня проекта:

    python scripts/optimize_images.py --source ../media --dest app/static/assets/img
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageOps

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DEST = BASE_DIR / "app" / "static" / "assets" / "img"
DEFAULT_SOURCE = BASE_DIR.parent / "media"

# (исходный файл, имя результата, целевая ширина)
IMAGE_MANIFEST: List[Tuple[str, str, int]] = [
    ("1679169355_design-pibig-info-p-sovr.jpg", "hero-hall.webp", 1600),
    ("864c66af3dc2cc0eb8166ba359500f25.jpg", "room-auditorium-1.webp", 1200),
    ("2692984_1632745507.225.jpg", "room-auditorium-2.webp", 1200),
    ("7621e0c3c1df2e3322f6222ff94e67f3.jpg", "room-coworking-1.webp", 1200),
    ("c522e46c4a9682fdebb.jpg", "room-coworking-2.webp", 1200),
    ("unnamed.jpg", "room-cinema.webp", 1200),
]

SOCIAL_MANIFEST: List[Tuple[str, str, int]] = [
    ("social/social.png", "about-team.webp", 900),
    ("social/soc.png", "social-networks.png", 320),
]
"""Изображения из соседнего каталога ``social`` (общие для проекта)."""

WEBP_QUALITY = 82


def resize_image(source: Path, target: Path, width: int, *, webp: bool) -> None:
    """Уменьшает изображение до заданной ширины и сохраняет в каталог назначения.

    Args:
        source: Путь к исходному изображению.
        target: Путь к результирующему файлу.
        width: Максимальная ширина в пикселях.
        webp: Сохранять ли в формате WebP.
    """
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image)
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGB")

        if image.width > width:
            height = round(image.height * width / image.width)
            image = image.resize((width, height), Image.LANCZOS)

        if webp:
            image.save(target, "WEBP", quality=WEBP_QUALITY, method=6)
        else:
            image.save(target, format=target.suffix.lstrip(".").upper())


def process_manifest(
    manifest: List[Tuple[str, str, int]], source_dir: Path, dest_dir: Path
) -> Dict[str, str]:
    """Обрабатывает набор изображений и возвращает отчёт о результатах.

    Args:
        manifest: Список описаний изображений.
        source_dir: Каталог с исходниками.
        dest_dir: Каталог назначения.

    Returns:
        Словарь ``имя файла -> статус``.
    """
    report: Dict[str, str] = {}
    dest_dir.mkdir(parents=True, exist_ok=True)

    for source_name, target_name, width in manifest:
        source = (source_dir / source_name).resolve()
        target = dest_dir / target_name

        if not source.exists():
            report[target_name] = f"пропущено (нет файла {source_name})"
            continue

        if target.exists() and target.stat().st_mtime >= source.stat().st_mtime:
            report[target_name] = "актуально"
            continue

        resize_image(
            source,
            target,
            width,
            webp=target.suffix.lower() == ".webp",
        )
        saved_kb = target.stat().st_size / 1024
        original_kb = source.stat().st_size / 1024
        report[target_name] = (
            f"готово ({original_kb:.0f} КБ -> {saved_kb:.0f} КБ, {width} px)"
        )

    return report


def parse_args(argv: List[str]) -> argparse.Namespace:
    """Разбирает аргументы командной строки.

    Args:
        argv: Аргументы запуска.

    Returns:
        Разобранные аргументы.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Каталог с исходными изображениями (по умолчанию: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=DEFAULT_DEST,
        help=f"Каталог назначения (по умолчанию: {DEFAULT_DEST})",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    """Точка входа скрипта.

    Args:
        argv: Аргументы командной строки.

    Returns:
        Код завершения процесса.
    """
    args = parse_args(argv or sys.argv[1:])

    report = process_manifest(IMAGE_MANIFEST, args.source, args.dest)
    report.update(process_manifest(SOCIAL_MANIFEST, BASE_DIR.parent, args.dest))

    for name, status in report.items():
        print(f"{name:<32} {status}")

    failed = [name for name, status in report.items() if status.startswith("пропущено")]
    if failed:
        print(f"\nНе обработано файлов: {len(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
