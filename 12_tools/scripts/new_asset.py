#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from vault_common import (
    cli_error,
    derive_asset_slug,
    ensure_area_exists,
    format_filename_datetime,
    parse_timestamp,
    resolve_root,
    validate_area_slug,
    validate_asset_category,
    validate_asset_topic_path,
)

PRIVATE_SOURCE_FOLDERS = (".creds", ".no-commit")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="File an area-local curated asset with a timestamped name.")
    parser.add_argument("category", metavar="CATEGORY", help="image, photo, screenshot, pdf, attachment, or import")
    parser.add_argument("source", metavar="SOURCE", help="source file to move or copy")
    parser.add_argument("--area", required=True, help="existing lowercase kebab-case area")
    parser.add_argument("--topic", required=True, help="slash-separated lowercase kebab-case topic path")
    parser.add_argument("--title", help="title used to derive the target slug")
    parser.add_argument("--slug", help="2 to 4 lowercase ASCII words separated by hyphens")
    parser.add_argument("--root", default=".", help="vault root; defaults to current directory")
    parser.add_argument("--timestamp", help="timezone-aware ISO datetime; defaults to now")
    parser.add_argument("--copy", action="store_true", help="copy the source instead of moving it")
    parser.add_argument("--dry-run", action="store_true", help="print planned action without changing files")
    parser.add_argument(
        "--sensitive-ok",
        action="store_true",
        help="allow a source under .creds/ or .no-commit/ after manual review",
    )
    return parser


def path_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def validate_source(source: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"{source}: source file does not exist")
    if source.is_dir():
        raise ValueError(f"{source}: SOURCE must be a file, not a directory")
    if not source.is_file():
        raise ValueError(f"{source}: SOURCE must be a regular file")
    if source.suffix == "":
        raise ValueError(f"{source}: SOURCE must have a file extension")


def validate_sensitive_source(root: Path, source_paths: tuple[Path, ...], sensitive_ok: bool) -> None:
    for folder in PRIVATE_SOURCE_FOLDERS:
        private_root = root / folder
        for source in source_paths:
            if path_under(source, private_root):
                if not sensitive_ok:
                    raise ValueError(f"{source}: source under {folder}/ requires --sensitive-ok")
                return


def plan_asset_path(
    root: Path,
    category_arg: str,
    source_arg: str,
    area: str,
    topic: str,
    title: str | None,
    slug: str | None,
    timestamp_text: str | None,
    sensitive_ok: bool,
) -> tuple[Path, Path]:
    validate_area_slug(area)
    ensure_area_exists(root, area)

    category = validate_asset_category(category_arg)
    topic_segments = validate_asset_topic_path(topic)
    timestamp = parse_timestamp(timestamp_text)

    raw_source = Path(source_arg).expanduser()
    lexical_source = raw_source if raw_source.is_absolute() else Path.cwd() / raw_source
    source = lexical_source.resolve()
    validate_source(source)
    validate_sensitive_source(root, (lexical_source.absolute(), source), sensitive_ok)

    asset_slug = derive_asset_slug(slug, title, source.stem)
    extension = source.suffix.lower()
    target = (
        root
        / "04_areas"
        / area
        / "assets"
        / category
        / Path(*topic_segments)
        / f"{format_filename_datetime(timestamp)}_{asset_slug}{extension}"
    )

    if target.exists():
        raise FileExistsError(f"{target.relative_to(root).as_posix()}: target already exists")

    return source, target


def create_asset(
    root: Path,
    category_arg: str,
    source_arg: str,
    area: str,
    topic: str,
    title: str | None,
    slug: str | None,
    timestamp_text: str | None,
    copy: bool,
    dry_run: bool,
    sensitive_ok: bool,
) -> Path:
    source, target = plan_asset_path(
        root,
        category_arg,
        source_arg,
        area,
        topic,
        title,
        slug,
        timestamp_text,
        sensitive_ok,
    )

    action = "copy" if copy else "move"
    if dry_run:
        print(f"Source: {source}")
        print(f"Action: {action}")
        print(f"Target: {target.relative_to(root).as_posix()}")
        return target

    target.parent.mkdir(parents=True, exist_ok=True)
    if copy:
        shutil.copy2(source, target)
    else:
        shutil.move(source, target)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = resolve_root(args.root)
        target = create_asset(
            root,
            args.category,
            args.source,
            args.area,
            args.topic,
            args.title,
            args.slug,
            args.timestamp,
            args.copy,
            args.dry_run,
            args.sensitive_ok,
        )
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        return cli_error(parser, str(exc))

    action = "Would create" if args.dry_run else "Created"
    print(f"{action} {target.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
