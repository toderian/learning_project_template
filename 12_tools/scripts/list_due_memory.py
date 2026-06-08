#!/usr/bin/env python3
"""List due note-level reviews and card-level memory items."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - fallback for minimal Python installs.
    yaml = None


@dataclass
class DueItem:
    kind: str
    path: str
    due: str
    title: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="Vault root. Defaults to the current directory.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Cutoff date in YYYY-MM-DD format.")
    parser.add_argument("--include-examples", action="store_true", help="Include notes tagged with example.")
    return parser.parse_args()


def is_due(value: str, cutoff: date) -> bool:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return False
    return parsed <= cutoff


def yaml_value_to_string(value: object) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    if isinstance(value, (list, dict)):
        return str(value)
    return str(value).strip()


def parse_fallback_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_fallback_tags(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return [
            item.strip().strip("'\"")
            for item in value[1:-1].split(",")
            if item.strip()
        ]
    if value:
        return [parse_fallback_scalar(value)]
    return []


def parse_frontmatter(text: str) -> dict[str, object]:
    if not text.startswith("---\n"):
        return {}
    lines = text.splitlines()
    end_index = None
    for index in range(1, len(lines)):
        if lines[index] == "---":
            end_index = index
            break
    if end_index is None:
        return {}

    frontmatter_text = "\n".join(lines[1:end_index])
    if yaml is not None:
        try:
            loaded = yaml.safe_load(frontmatter_text) if frontmatter_text.strip() else {}
        except Exception:
            return {}
        if isinstance(loaded, dict):
            return {str(key): value for key, value in loaded.items()}
        return {}

    data: dict[str, object] = {}
    for line in lines[1:end_index]:
        if ":" not in line or line.strip().startswith("- "):
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        data[key] = parse_fallback_tags(value) if key == "tags" else parse_fallback_scalar(value)
    return data


def frontmatter_scalar(frontmatter: dict[str, object], key: str) -> str:
    return yaml_value_to_string(frontmatter.get(key, ""))


def is_example_note(frontmatter: dict[str, object]) -> bool:
    tags = frontmatter.get("tags", [])
    if isinstance(tags, list):
        return any(str(tag).strip() == "example" for tag in tags)
    if isinstance(tags, str):
        return "example" in parse_fallback_tags(tags)
    return False


def iter_non_fenced_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    in_fence = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append((line_number, line))
    return lines


def heading_for_non_fenced_line(lines: list[tuple[int, str]], index: int) -> str:
    for current in range(index, -1, -1):
        line = lines[current][1].strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return "Untitled card"


def collect_due(root: Path, cutoff: date, include_examples: bool = False) -> list[DueItem]:
    items: list[DueItem] = []
    for path in sorted(root.rglob("*.md")):
        if ".git" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(text)
        if is_example_note(frontmatter) and not include_examples:
            continue
        review_after = frontmatter_scalar(frontmatter, "review_after")
        if review_after and is_due(review_after, cutoff):
            title = next((line.lstrip("#").strip() for line in text.splitlines() if line.startswith("# ")), path.stem)
            items.append(DueItem("note", relative, review_after, title))

        lines = iter_non_fenced_lines(text)
        for index, (_line_number, line) in enumerate(lines):
            match = re.match(r"^\s*due::\s*(\d{4}-\d{2}-\d{2})\s*$", line)
            if not match:
                continue
            due = match.group(1)
            if is_due(due, cutoff):
                items.append(DueItem("card", relative, due, heading_for_non_fenced_line(lines, index)))
    return sorted(items, key=lambda item: (item.due, item.path, item.kind, item.title))


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    cutoff = datetime.strptime(args.date, "%Y-%m-%d").date()
    items = collect_due(root, cutoff, include_examples=args.include_examples)

    if not items:
        print(f"No due memory items on or before {cutoff.isoformat()}.")
        return 0

    for item in items:
        print(f"{item.due}\t{item.kind}\t{item.path}\t{item.title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
