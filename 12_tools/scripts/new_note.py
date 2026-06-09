#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vault_common import (
    SchemaRow,
    cli_error,
    ensure_area_exists,
    format_filename_datetime,
    parse_schema,
    parse_timestamp,
    render_template,
    resolve_root,
    route_to_directory,
    slug_from_title,
    validate_area_slug,
    validate_note_slug,
)

GLOBAL_NOTE_TYPES = {"inbox", "agent_draft"}
STRUCTURAL_TYPES = {"area", "asset", "archive", "agent_memory", "system", "tool"}
GLOBAL_UNSUPPORTED_TYPES = {
    "journal",
    "weekly_review",
    "monthly_review",
    "quarterly_review",
    "yearly_review",
    "decision",
    "reflection",
    "study_session",
    "practice_log",
    "error_log",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a timestamped Markdown note from the schema template.")
    parser.add_argument("note_type", metavar="TYPE", help="schema note type")
    parser.add_argument("title", metavar="TITLE", help="note title")
    parser.add_argument("--area", help="required for area-local note types; optional for area-local inbox")
    parser.add_argument("--slug", help="2 to 4 lowercase ASCII words separated by hyphens")
    parser.add_argument("--root", default=".", help="vault root; defaults to current directory")
    parser.add_argument("--timestamp", help="timezone-aware ISO datetime; defaults to now")
    parser.add_argument("--dry-run", action="store_true", help="print planned path without writing")
    return parser


def note_route(row_default_folder: str, note_type: str, area: str | None) -> tuple[str, str | None]:
    if note_type == "inbox" and area is not None:
        validate_area_slug(area)
        return f"04_areas/{area}/inbox/", area
    return row_default_folder, area


def validate_supported_note_type(note_type: str, rows: dict[str, SchemaRow]) -> None:
    if note_type not in rows:
        raise ValueError(f"unsupported note type '{note_type}'")
    if note_type in STRUCTURAL_TYPES:
        if note_type == "area":
            raise ValueError("type 'area' is created with create_area.py")
        raise ValueError(f"type '{note_type}' is not supported by new_note.py")
    if note_type in GLOBAL_UNSUPPORTED_TYPES:
        raise ValueError(f"type '{note_type}' is not supported by new_note.py")


def create_note(
    root: Path,
    note_type: str,
    title: str,
    area: str | None,
    slug: str | None,
    timestamp_text: str | None,
    dry_run: bool,
) -> Path:
    rows = parse_schema(root)
    validate_supported_note_type(note_type, rows)
    row = rows[note_type]

    if note_type not in GLOBAL_NOTE_TYPES and "*" not in row.default_folder:
        raise ValueError(f"type '{note_type}' is not an area-local note type")
    if note_type == "agent_draft" and area is not None:
        raise ValueError("--area is not supported for agent_draft")

    route, route_area = note_route(row.default_folder, note_type, area)
    if "*" in route or route_area is not None:
        if route_area is None:
            raise ValueError("--area is required for area-local note types")
        ensure_area_exists(root, route_area)

    if row.default_template == "none":
        raise ValueError(f"type '{note_type}' does not have a Markdown template")
    template_path = root / "11_templates" / row.default_template
    if not template_path.is_file():
        raise FileNotFoundError(f"11_templates/{row.default_template} is missing")

    timestamp = parse_timestamp(timestamp_text)
    note_slug = validate_note_slug(slug) if slug is not None else slug_from_title(title)
    directory = route_to_directory(root, route, route_area)
    target = directory / f"{format_filename_datetime(timestamp)}_{note_slug}.md"
    rendered = render_template(template_path.read_text(encoding="utf-8"), title, timestamp)

    if target.exists():
        raise FileExistsError(f"{target.relative_to(root).as_posix()}: target already exists")
    if dry_run:
        print(target.relative_to(root).as_posix())
        return target

    directory.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = resolve_root(args.root)
        target = create_note(
            root,
            args.note_type,
            args.title,
            args.area,
            args.slug,
            args.timestamp,
            args.dry_run,
        )
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        return cli_error(parser, str(exc))

    action = "Would create" if args.dry_run else "Created"
    print(f"{action} {target.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
