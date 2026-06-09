#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BUCHAREST = ZoneInfo("Europe/Bucharest")

AREA_SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
NOTE_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){1,3}$")


@dataclass(frozen=True)
class SchemaRow:
    note_type: str
    default_folder: str
    default_template: str


def resolve_root(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


def parse_timestamp(value: str | None) -> datetime:
    if value is None:
        parsed = datetime.now(tz=BUCHAREST)
    else:
        normalized = value.removesuffix("Z") + "+00:00" if value.endswith("Z") else value
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError("--timestamp must be a valid ISO 8601 datetime") from exc
        if parsed.tzinfo is None:
            raise ValueError("--timestamp must include a timezone offset")
    return parsed.astimezone(BUCHAREST)


def format_frontmatter_datetime(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def format_filename_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H%M%S%z")


def validate_area_slug(value: str) -> str:
    if not AREA_SLUG_PATTERN.fullmatch(value):
        raise ValueError("AREA must be lowercase kebab-case, for example web-security")
    return value


def validate_note_slug(value: str) -> str:
    if not NOTE_SLUG_PATTERN.fullmatch(value):
        raise ValueError("slug must be 2 to 4 lowercase ASCII words separated by hyphens")
    return value


def title_from_slug(value: str) -> str:
    return " ".join(part.capitalize() for part in value.split("-"))


def slug_from_title(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    words = re.findall(r"[A-Za-z0-9]+", normalized.lower())
    if len(words) < 2:
        raise ValueError("could not derive a 2 to 4 word slug from TITLE; pass --slug")
    return validate_note_slug("-".join(words[:4]))


def parse_code_cell(cell: str, column: str, line: str) -> str:
    if cell == "none":
        return cell
    if not (cell.startswith("`") and cell.endswith("`")):
        raise ValueError(f"00_system/schema.md: {column} cell must be backticked in row: {line}")
    return cell.strip("`")


def parse_schema(root: Path) -> dict[str, SchemaRow]:
    schema_path = root / "00_system/schema.md"
    if not schema_path.exists():
        raise FileNotFoundError("00_system/schema.md is missing")

    rows: dict[str, SchemaRow] = {}
    for line in schema_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            raise ValueError(f"00_system/schema.md: malformed schema table row: {line}")
        note_type = parse_code_cell(cells[0], "Type", line)
        default_folder = parse_code_cell(cells[2], "Default Folder", line)
        default_template = parse_code_cell(cells[3], "Default Template", line)
        if note_type in rows:
            raise ValueError(f"00_system/schema.md: duplicate schema type '{note_type}'")
        rows[note_type] = SchemaRow(note_type, default_folder, default_template)

    if not rows:
        raise ValueError("00_system/schema.md: no note types parsed from schema table")
    return rows


def render_template(template_text: str, title: str, timestamp: datetime) -> str:
    timestamp_text = format_frontmatter_datetime(timestamp)
    lines = template_text.splitlines()
    in_frontmatter = bool(lines and lines[0] == "---")
    frontmatter_closed = not in_frontmatter
    replaced_h1 = False

    for index, line in enumerate(lines):
        if index > 0 and in_frontmatter and line == "---":
            frontmatter_closed = True
            in_frontmatter = False
            continue
        if in_frontmatter and line.startswith(("created:", "updated:")):
            key = line.split(":", 1)[0]
            lines[index] = f"{key}: {timestamp_text}"
            continue
        if frontmatter_closed and not replaced_h1 and line.startswith("# "):
            lines[index] = f"# {title}"
            replaced_h1 = True

    if not replaced_h1:
        lines.append(f"# {title}")

    return "\n".join(lines).rstrip() + "\n"


def route_to_directory(root: Path, route: str, area: str | None) -> Path:
    if "*" in route:
        if area is None:
            raise ValueError("--area is required for area-local note types")
        validate_area_slug(area)
        route = route.replace("*", area, 1)
    elif area is not None and not route.startswith(f"04_areas/{area}/"):
        raise ValueError("--area is only supported for area-local routes and inbox notes")

    if route.endswith(".md"):
        raise ValueError("route points to a fixed file, not a note directory")
    return root / route.strip("/")


def ensure_area_exists(root: Path, area: str) -> None:
    validate_area_slug(area)
    marker = root / "04_areas" / area / "README.md"
    if not marker.is_file():
        raise FileNotFoundError(f"area '{area}' does not exist at 04_areas/{area}/README.md")


def write_file(path: Path, text: str, dry_run: bool) -> None:
    if path.exists():
        raise FileExistsError(f"{path}: target already exists")
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def cli_error(parser: argparse.ArgumentParser, message: str) -> int:
    parser.exit(2, f"{parser.prog}: error: {message}\n")
