#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vault_common import (
    cli_error,
    parse_timestamp,
    render_template,
    resolve_root,
    title_from_slug,
    validate_area_slug,
)

AREA_DIRECTORIES = [
    "inbox",
    "resources",
    "resources/books",
    "resources/courses",
    "resources/documentation",
    "resources/papers",
    "resources/videos",
    "notes",
    "notes/fleeting",
    "notes/literature",
    "notes/atomic",
    "notes/wiki",
    "notes/mocs",
    "notes/synthesis",
    "memory",
    "memory/spaced_repetition",
    "memory/retrieval_practice",
    "memory/review_logs",
    "projects",
    "outputs",
    "outputs/summaries",
    "outputs/reports",
    "outputs/essays",
    "outputs/study_plans",
    "assets",
    "assets/attachments",
    "assets/images",
    "assets/imports",
    "archive",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a new 04_areas/<area>/ skeleton.")
    parser.add_argument("area", metavar="AREA", help="lowercase kebab-case area slug")
    parser.add_argument("--title", help="README title; defaults to title-cased AREA")
    parser.add_argument("--root", default=".", help="vault root; defaults to current directory")
    parser.add_argument("--timestamp", help="timezone-aware ISO datetime; defaults to now")
    parser.add_argument("--dry-run", action="store_true", help="print planned paths without writing")
    return parser


def create_area(root: Path, area: str, title: str | None, timestamp_text: str | None, dry_run: bool) -> Path:
    validate_area_slug(area)
    area_root = root / "04_areas" / area
    readme_path = area_root / "README.md"
    if area_root.exists():
        raise FileExistsError(f"04_areas/{area}: area already exists")

    template_path = root / "11_templates/area.md"
    if not template_path.is_file():
        raise FileNotFoundError("11_templates/area.md is missing")

    timestamp = parse_timestamp(timestamp_text)
    rendered = render_template(template_path.read_text(encoding="utf-8"), title or title_from_slug(area), timestamp)

    if dry_run:
        print(readme_path.relative_to(root).as_posix())
        for directory in AREA_DIRECTORIES:
            print((area_root / directory).relative_to(root).as_posix() + "/")
        return readme_path

    for directory in AREA_DIRECTORIES:
        (area_root / directory).mkdir(parents=True, exist_ok=True)
    readme_path.write_text(rendered, encoding="utf-8")
    return readme_path


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = resolve_root(args.root)
        readme_path = create_area(root, args.area, args.title, args.timestamp, args.dry_run)
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        return cli_error(parser, str(exc))

    action = "Would create" if args.dry_run else "Created"
    print(f"{action} {readme_path.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
