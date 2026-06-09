#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BUCHAREST = ZoneInfo("Europe/Bucharest")

AREA_SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
NOTE_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){1,3}$")
ASSET_TOPIC_SEGMENT_PATTERN = AREA_SLUG_PATTERN
ASSET_CATEGORY_ALIASES = {
    "attachment": "attachments",
    "attachments": "attachments",
    "dataset": "imports",
    "export": "imports",
    "image": "images",
    "images": "images",
    "import": "imports",
    "imports": "imports",
    "pdf": "attachments",
    "photo": "images",
    "screenshot": "images",
}
ASSET_CATEGORIES = frozenset(sorted(set(ASSET_CATEGORY_ALIASES.values())))
ASSET_EXTENSIONS_BY_CATEGORY = {
    "attachments": frozenset(
        {
            ".docx",
            ".epub",
            ".pdf",
            ".pptx",
            ".txt",
            ".xlsx",
            ".zip",
        }
    ),
    "images": frozenset(
        {
            ".gif",
            ".jpeg",
            ".jpg",
            ".png",
            ".svg",
            ".webp",
        }
    ),
    "imports": frozenset(
        {
            ".csv",
            ".har",
            ".htm",
            ".html",
            ".json",
            ".jsonl",
            ".ndjson",
            ".txt",
            ".xml",
            ".yaml",
            ".yml",
            ".zip",
        }
    ),
}
PRIVATE_SCAN_ROOTS = frozenset({".creds", ".no-commit"})
FALLBACK_EXCLUDED_PARTS = frozenset(
    {
        ".cache",
        ".git",
        ".pytest_cache",
        ".venv",
        "__pycache__",
        "node_modules",
        "venv",
    }
) | PRIVATE_SCAN_ROOTS


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


def validate_asset_category(value: str) -> str:
    category = ASSET_CATEGORY_ALIASES.get(value.lower())
    if category is None:
        valid = ", ".join(sorted(ASSET_CATEGORY_ALIASES))
        raise ValueError(f"CATEGORY must be one of {valid}")
    return category


def validate_asset_extension(category: str, extension: str) -> str:
    if not extension:
        raise ValueError("asset must have a lowercase supported file extension")
    if extension != extension.lower():
        raise ValueError("asset extension must be lowercase")
    supported = ASSET_EXTENSIONS_BY_CATEGORY[category]
    if extension not in supported:
        valid = ", ".join(sorted(supported))
        raise ValueError(f"asset extension '{extension}' is not supported for {category}; expected one of {valid}")
    return extension


def validate_asset_topic_path(value: str) -> tuple[str, ...]:
    segments = value.split("/")
    if not value or any(segment == "" for segment in segments):
        raise ValueError("--topic must be a slash-separated lowercase kebab-case path")
    for segment in segments:
        if not ASSET_TOPIC_SEGMENT_PATTERN.fullmatch(segment):
            raise ValueError("--topic must be a slash-separated lowercase kebab-case path")
    return tuple(segments)


def title_from_slug(value: str) -> str:
    return " ".join(part.capitalize() for part in value.split("-"))


def slug_from_text(value: str, source_name: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    words = re.findall(r"[A-Za-z0-9]+", normalized.lower())
    if len(words) < 2:
        raise ValueError(f"could not derive a 2 to 4 word slug from {source_name}; pass --slug")
    return validate_note_slug("-".join(words[:4]))


def slug_from_title(title: str) -> str:
    return slug_from_text(title, "TITLE")


def derive_asset_slug(slug: str | None, title: str | None, source_stem: str) -> str:
    if slug is not None:
        return validate_note_slug(slug)
    if title is not None:
        return slug_from_text(title, "TITLE")
    return slug_from_text(source_stem, "source filename")


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


def git_ls_files(root: Path, *args: str) -> set[str] | None:
    result = subprocess.run(
        ["git", "ls-files", "-z", *args],
        cwd=root,
        check=False,
        text=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        return None
    return {
        item.decode("utf-8")
        for item in result.stdout.split(b"\0")
        if item
    }


def is_private_relative_path(relative: str) -> bool:
    first = relative.split("/", 1)[0]
    return first in PRIVATE_SCAN_ROOTS


def _fallback_scan_paths(root: Path) -> set[str]:
    relatives: set[str] = set()
    for path in root.rglob("*"):
        try:
            relative_path = path.relative_to(root)
        except ValueError:
            continue
        if set(relative_path.parts) & FALLBACK_EXCLUDED_PARTS:
            continue
        relatives.add(relative_path.as_posix())
    return relatives


def discover_tracked_unignored_paths(root: Path) -> tuple[Path, ...]:
    tracked = git_ls_files(root, "--cached")
    unignored = git_ls_files(root, "--others", "--exclude-standard")
    relatives = _fallback_scan_paths(root) if tracked is None or unignored is None else tracked | unignored
    paths = [
        root / relative
        for relative in sorted(relatives)
        if not is_private_relative_path(relative)
    ]
    return tuple(paths)


def safe_scan_files(root: Path) -> tuple[Path, ...]:
    files: list[Path] = []
    for path in discover_tracked_unignored_paths(root):
        if path.is_symlink():
            continue
        if path.is_file():
            files.append(path)
    return tuple(sorted(files, key=lambda path: path.relative_to(root).as_posix()))


def scan_symlinks(root: Path) -> tuple[Path, ...]:
    symlinks = [
        path
        for path in discover_tracked_unignored_paths(root)
        if path.is_symlink()
    ]
    return tuple(sorted(symlinks, key=lambda path: path.relative_to(root).as_posix()))


def safe_scan_paths(root: Path) -> tuple[Path, ...]:
    paths: set[Path] = set(safe_scan_files(root))
    paths.update(scan_symlinks(root))
    for path in tuple(paths):
        parent = path.parent
        while parent != root:
            try:
                parent.relative_to(root)
            except ValueError:
                break
            paths.add(parent)
            parent = parent.parent
    return tuple(sorted(paths, key=lambda path: path.relative_to(root).as_posix()))


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
