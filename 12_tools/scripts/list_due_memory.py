#!/usr/bin/env python3
"""List due note-level reviews and card-level memory items."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


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
    return parser.parse_args()


def is_due(value: str, cutoff: date) -> bool:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return False
    return parsed <= cutoff


def parse_frontmatter(text: str) -> dict[str, str]:
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

    data: dict[str, str] = {}
    for line in lines[1:end_index]:
        if ":" not in line or line.strip().startswith("- "):
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


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


def collect_due(root: Path, cutoff: date) -> list[DueItem]:
    items: list[DueItem] = []
    for path in sorted(root.rglob("*.md")):
        if ".git" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(text)
        review_after = frontmatter.get("review_after", "")
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
    items = collect_due(root, cutoff)

    if not items:
        print(f"No due memory items on or before {cutoff.isoformat()}.")
        return 0

    for item in items:
        print(f"{item.due}\t{item.kind}\t{item.path}\t{item.title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
