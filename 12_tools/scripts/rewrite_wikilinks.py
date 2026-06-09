#!/usr/bin/env python3
"""Rewrite inbound Obsidian wikilinks after an approved note move or rename."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from vault_common import safe_scan_files

WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Vault root. Defaults to the current directory.")
    parser.add_argument("--from", dest="old", required=True, help="Old note path or basename, with or without .md.")
    parser.add_argument("--to", dest="new", required=True, help="New note path or basename, with or without .md.")
    parser.add_argument("--write", action="store_true", help="Write changes. Without this flag, runs as a dry run.")
    return parser.parse_args()


def normalize_target(value: str) -> str:
    value = value.strip().removesuffix(".md").strip("/")
    return value


def markdown_note_index(root: Path) -> dict[str, list[str]]:
    by_stem: dict[str, list[str]] = {}
    for path in safe_scan_files(root):
        if path.suffix != ".md":
            continue
        relative = path.relative_to(root).with_suffix("").as_posix()
        by_stem.setdefault(path.stem, []).append(relative)
    return by_stem


def target_variants(root: Path, value: str) -> set[str]:
    normalized = normalize_target(value)
    basename = Path(normalized).name
    by_stem = markdown_note_index(root)
    stem_matches = by_stem.get(basename, [])

    if "/" not in normalized:
        if len(stem_matches) > 1:
            matches = ", ".join(stem_matches)
            raise SystemExit(f"--from '{value}' is ambiguous; use a full path. Matches: {matches}")
        return {normalized}

    variants = {normalized}
    if len(stem_matches) == 1 and stem_matches[0] == normalized:
        variants.add(basename)
    elif not stem_matches:
        variants.add(basename)
    return variants


def rewrite_line(line: str, old_variants: set[str], new_target: str) -> tuple[str, int]:
    changes = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal changes
        inner = match.group(1)
        target_and_fragment, alias = (inner.split("|", 1) + [""])[:2] if "|" in inner else (inner, "")
        target, fragment = (target_and_fragment.split("#", 1) + [""])[:2] if "#" in target_and_fragment else (target_and_fragment, "")
        normalized = normalize_target(target)
        if normalized not in old_variants:
            return match.group(0)

        changes += 1
        rebuilt = new_target
        if fragment:
            rebuilt = f"{rebuilt}#{fragment}"
        if alias:
            rebuilt = f"{rebuilt}|{alias}"
        return f"[[{rebuilt}]]"

    return WIKILINK.sub(replace, line), changes


def rewrite_text(text: str, old_variants: set[str], new_target: str) -> tuple[str, int]:
    changes = 0
    rewritten_lines: list[str] = []
    in_fence = False

    for line in text.splitlines(keepends=True):
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
            rewritten_lines.append(line)
            continue
        if in_fence:
            rewritten_lines.append(line)
            continue
        rewritten, line_changes = rewrite_line(line, old_variants, new_target)
        changes += line_changes
        rewritten_lines.append(rewritten)

    return "".join(rewritten_lines), changes


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    old_variants = target_variants(root, args.old)
    new_target = normalize_target(args.new)
    total = 0

    for path in safe_scan_files(root):
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        rewritten, changes = rewrite_text(text, old_variants, new_target)
        if not changes:
            continue
        total += changes
        relative = path.relative_to(root).as_posix()
        print(f"{relative}: {changes} wikilink update(s)")
        if args.write:
            path.write_text(rewritten, encoding="utf-8")

    mode = "updated" if args.write else "would update"
    print(f"{mode} {total} wikilink(s)")
    if not args.write:
        print("Dry run only. Re-run with --write after approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
