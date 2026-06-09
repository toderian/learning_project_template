#!/usr/bin/env python3
from __future__ import annotations

import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - fallback for minimal Python installs.
    yaml = None

ROOT = Path.cwd()
ERRORS: list[str] = []
WARNINGS: list[str] = []
SCAN_FILES_CACHE: list[Path] | None = None
SCAN_PATHS_CACHE: list[Path] | None = None

SCALAR_FRONTMATTER_FIELDS = {
    "type",
    "status",
    "created",
    "updated",
    "review_after",
    "confidence",
    "source",
    "url",
    "author",
}


@dataclass(frozen=True)
class SchemaRow:
    note_type: str
    default_folder: str
    default_template: str


@dataclass(frozen=True)
class ValidationResult:
    errors: list[str]
    warnings: list[str]


TIMESTAMPED_NAME_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{6}[+-]\d{4}_[a-z0-9]+(?:-[a-z0-9]+){1,3}$"
)

PRIVATE_FOLDERS = (".creds", ".no-commit")
REQUIRED_GITIGNORE_PATTERNS = {
    ".creds/": ".creds/.vault-validation-probe",
    ".no-commit/": ".no-commit/.vault-validation-probe",
    ".env": ".env",
    ".env.*": ".env.local",
}


def reset_context(root: str | Path) -> None:
    global ROOT, ERRORS, WARNINGS, SCAN_FILES_CACHE, SCAN_PATHS_CACHE
    ROOT = Path(root).resolve()
    ERRORS = []
    WARNINGS = []
    SCAN_FILES_CACHE = None
    SCAN_PATHS_CACHE = None


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def error(message: str) -> None:
    ERRORS.append(message)


def warn(message: str) -> None:
    WARNINGS.append(message)


def git_ls_files(*args: str) -> set[str] | None:
    result = subprocess.run(
        ["git", "ls-files", "-z", *args],
        cwd=ROOT,
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


def scan_files() -> list[Path]:
    global SCAN_FILES_CACHE
    if SCAN_FILES_CACHE is not None:
        return SCAN_FILES_CACHE

    tracked = git_ls_files("--cached")
    unignored = git_ls_files("--others", "--exclude-standard")
    if tracked is None or unignored is None:
        files = [
            path
            for path in ROOT.rglob("*")
            if ".git" not in path.relative_to(ROOT).parts and path.is_file()
        ]
    else:
        files = [
            ROOT / relative
            for relative in sorted(tracked | unignored)
            if (ROOT / relative).is_file()
        ]

    SCAN_FILES_CACHE = sorted(files, key=rel)
    return SCAN_FILES_CACHE


def all_paths() -> list[Path]:
    global SCAN_PATHS_CACHE
    if SCAN_PATHS_CACHE is not None:
        return SCAN_PATHS_CACHE

    paths: set[Path] = set(scan_files())
    for file_path in scan_files():
        parent = file_path.parent
        while parent != ROOT:
            try:
                parent.relative_to(ROOT)
            except ValueError:
                break
            paths.add(parent)
            parent = parent.parent

    SCAN_PATHS_CACHE = sorted(paths, key=rel)
    return SCAN_PATHS_CACHE


def all_files() -> list[Path]:
    return scan_files()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_scan_text(path: Path) -> str:
    with path.open("rb") as handle:
        data = handle.read(30 * 1024 * 1024)
    return data.decode("utf-8", errors="ignore")


def is_iso_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def is_iso_datetime(value: str) -> bool:
    if "T" not in value:
        return False
    normalized = value.removesuffix("Z") + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def is_iso_date_or_datetime(value: str) -> bool:
    return is_iso_date(value) or is_iso_datetime(value)


def yaml_value_to_string(key: str, value: object, path: Path) -> str:
    if value is None:
        return ""
    if key in SCALAR_FRONTMATTER_FIELDS and isinstance(value, (list, dict)):
        error(f"{rel(path)}: scalar frontmatter field '{key}' must not be a YAML list or mapping")
        return ""
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    if isinstance(value, (list, dict)):
        return str(value)
    return str(value).strip()


def validate_yaml_subset(frontmatter_text: str, path: Path) -> dict[str, str] | None:
    data: dict[str, str] = {}
    current_key = ""
    for line_number, line in enumerate(frontmatter_text.splitlines(), start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if current_key in SCALAR_FRONTMATTER_FIELDS:
                error(f"{rel(path)}:{line_number}: scalar frontmatter field '{current_key}' must not be a YAML list")
            continue
        if ":" not in line:
            error(f"{rel(path)}:{line_number}: invalid frontmatter line")
            return None
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if not key:
            error(f"{rel(path)}:{line_number}: empty frontmatter key")
            return None
        if key in data:
            error(f"{rel(path)}:{line_number}: duplicate frontmatter key '{key}'")
        if value.count("[") != value.count("]") or value.count("{") != value.count("}"):
            error(f"{rel(path)}:{line_number}: invalid YAML flow collection")
            return None
        if value.startswith("[") and not value.endswith("]"):
            error(f"{rel(path)}:{line_number}: invalid YAML flow list")
            return None
        if value.startswith("{") and not value.endswith("}"):
            error(f"{rel(path)}:{line_number}: invalid YAML flow mapping")
            return None
        if key in SCALAR_FRONTMATTER_FIELDS and (value.startswith("[") or value.startswith("{")):
            error(f"{rel(path)}:{line_number}: scalar frontmatter field '{key}' must not be a YAML list or mapping")
        data[key] = value
    return data


def parse_frontmatter(text: str, path: Path) -> tuple[dict[str, str], str] | None:
    if not text.startswith("---\n"):
        return None
    lines = text.splitlines()
    end_index = None
    for index in range(1, len(lines)):
        if lines[index] == "---":
            end_index = index
            break
    if end_index is None:
        error(f"{rel(path)}: frontmatter starts but never closes")
        return None

    frontmatter_text = "\n".join(lines[1:end_index])
    seen_keys: set[str] = set()
    for line_number, line in enumerate(frontmatter_text.splitlines(), start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            continue
        if ":" not in line:
            error(f"{rel(path)}:{line_number}: invalid frontmatter line")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if not key:
            error(f"{rel(path)}:{line_number}: empty frontmatter key")
            continue
        if key in seen_keys:
            error(f"{rel(path)}:{line_number}: duplicate frontmatter key '{key}'")
        seen_keys.add(key)

    data: dict[str, str] = {}
    if yaml is not None:
        try:
            loaded = yaml.safe_load(frontmatter_text) if frontmatter_text.strip() else {}
        except Exception as exc:
            error(f"{rel(path)}: invalid YAML frontmatter: {exc}")
            loaded = {}
        if loaded is None:
            loaded = {}
        if not isinstance(loaded, dict):
            error(f"{rel(path)}: frontmatter must be a YAML mapping")
            loaded = {}
        data = {str(key): yaml_value_to_string(str(key), value, path) for key, value in loaded.items()}
    else:
        parsed = validate_yaml_subset(frontmatter_text, path)
        if parsed is not None:
            data = parsed

    body = "\n".join(lines[end_index + 1 :])
    return data, body


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


def text_without_fenced_blocks(text: str) -> str:
    return "\n".join(line for _line_number, line in iter_non_fenced_lines(text))


def parse_code_cell(cell: str, column: str, line: str) -> str:
    if cell == "none":
        return cell
    if not (cell.startswith("`") and cell.endswith("`")):
        error(f"00_system/schema.md: {column} cell must be backticked in row: {line}")
        return cell.strip("`")
    return cell.strip("`")


def route_has_wildcard(route: str) -> bool:
    return "*" in route.strip("/").split("/")


def route_static_base(route: str) -> Path:
    parts: list[str] = []
    for part in route.strip("/").split("/"):
        if part == "*":
            break
        parts.append(part)
    return Path(*parts) if parts else Path(".")


def parse_schema() -> dict[str, SchemaRow]:
    schema_path = ROOT / "00_system/schema.md"
    if not schema_path.exists():
        error("00_system/schema.md is missing")
        return {}

    rows: dict[str, SchemaRow] = {}

    for line in read_text(schema_path).splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            error(f"00_system/schema.md: malformed schema table row: {line}")
            continue
        note_type = parse_code_cell(cells[0], "Type", line)
        default_folder = parse_code_cell(cells[2], "Default Folder", line)
        default_template = parse_code_cell(cells[3], "Default Template", line)

        if note_type in rows:
            error(f"00_system/schema.md: duplicate schema type '{note_type}'")

        if route_has_wildcard(default_folder):
            base = ROOT / route_static_base(default_folder)
            if not base.exists():
                error(
                    f"00_system/schema.md: static base '{rel(base)}' for route "
                    f"'{default_folder}' is missing"
                )
        else:
            target = ROOT / default_folder
            if default_folder.endswith(".md"):
                if not target.is_file():
                    error(f"00_system/schema.md: default file '{default_folder}' for type '{note_type}' is missing")
            elif not target.is_dir():
                error(f"00_system/schema.md: default folder '{default_folder}' for type '{note_type}' is missing")

        rows[note_type] = SchemaRow(
            note_type=note_type,
            default_folder=default_folder,
            default_template=default_template,
        )

    if not rows:
        error("00_system/schema.md: no note types parsed from schema table")

    return rows


def note_schema_exempt(path: Path) -> bool:
    relative = rel(path)
    if path.name == "README.md":
        return True
    if relative in {"AGENTS.md", "CLAUDE.md"}:
        return True
    if relative.startswith("_prompts/"):
        return True
    if relative.startswith(".agents/skills/") or relative.startswith(".claude/skills/"):
        return True
    return False


def default_folder_exempt(path: Path) -> bool:
    return rel(path) == "10_agents/tests/prompt_injection_canary.md"


def route_segment_matches(pattern_segment: str, path_segment: str) -> bool:
    return pattern_segment == "*" or pattern_segment == path_segment


def path_matches_route(relative: str, route: str) -> bool:
    pattern_parts = [part for part in route.strip("/").split("/") if part]
    path_parts = [part for part in relative.strip("/").split("/") if part]

    if route.endswith("/"):
        if len(path_parts) <= len(pattern_parts):
            return False
        return all(
            route_segment_matches(pattern_part, path_part)
            for pattern_part, path_part in zip(pattern_parts, path_parts)
        )

    if len(path_parts) != len(pattern_parts):
        return False
    return all(
        route_segment_matches(pattern_part, path_part)
        for pattern_part, path_part in zip(pattern_parts, path_parts)
    )


def check_paths(paths: list[Path]) -> None:
    for path in paths:
        relative = rel(path)
        if " " in relative:
            error(f"{relative}: path contains a space")

    forbidden_exact = {
        ".env",
        ".mcp.json",
        ".codex/config.toml",
        ".codex/hooks.json",
        ".claude/settings.json",
        ".claude/settings.local.json",
        ".obsidian/hotkeys.json",
        ".obsidian/community-plugins.json",
    }
    forbidden_prefixes = {
        ".obsidian/plugins/",
        ".obsidian/themes/",
        "vector_db/",
        "transcripts_db/",
        "chroma/",
        "basic_memory/",
        "mempalace/",
        "MemPalace/",
        "04_areas/*/outputs/agent_drafts/tmp/",
    }
    removed_global_prefixes = {
        "03_projects/",
        "05_resources/",
        "06_knowledge/",
        "07_memory/",
        "08_outputs/",
        "09_assets/",
        "99_archive/",
    }
    forbidden_parts = {
        "__pycache__",
        ".pytest_cache",
        ".cache",
        "node_modules",
    }

    allowed_obsidian = {
        ".obsidian/core-plugins.json",
        ".obsidian/templates.json",
        ".obsidian/daily-notes.json",
        ".obsidian/app.json",
    }

    for path in paths:
        relative = rel(path)
        parts = set(path.relative_to(ROOT).parts)
        if relative in forbidden_exact:
            error(f"{relative}: forbidden runtime or secret path")
        if fnmatch.fnmatch(relative, ".env.*"):
            error(f"{relative}: forbidden env file")
        if fnmatch.fnmatch(relative, ".obsidian/workspace*.json"):
            error(f"{relative}: Obsidian workspace state must not be committed")
        if any(path_matches_route(relative, prefix) for prefix in forbidden_prefixes):
            error(f"{relative}: forbidden runtime directory content")
        if any(relative.startswith(prefix) for prefix in removed_global_prefixes):
            error(f"{relative}: removed global topic layer; use 04_areas/<area>/ instead")
        if forbidden_parts & parts:
            error(f"{relative}: forbidden generated or dependency artifact")
        if path.is_file() and relative.startswith(".obsidian/") and relative not in allowed_obsidian:
            error(f"{relative}: .obsidian file is not in the allowlist")
        if path.is_file() and relative.startswith("12_tools/outputs/") and relative != "12_tools/outputs/README.md":
            error(f"{relative}: generated tool output must not be committed")
        if path.is_file() and (relative.endswith(".sqlite") or relative.endswith(".db") or relative.endswith(".log")):
            error(f"{relative}: generated database or log file must not be committed")


def check_gitignore() -> None:
    gitignore = ROOT / ".gitignore"
    if not gitignore.exists():
        error(".gitignore is missing")
        return

    gitignore_lines = read_text(gitignore).splitlines()
    normalized_patterns: set[str] = set()
    for line_number, line in enumerate(gitignore_lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("!") and not stripped.startswith("\\!"):
            pattern = stripped[1:].lstrip("/")
            if any(pattern == folder or pattern.startswith(f"{folder}/") for folder in PRIVATE_FOLDERS):
                error(f".gitignore:{line_number}: private folder unignore pattern is forbidden")
            continue
        normalized_patterns.add(stripped.lstrip("/"))

    for required_pattern, probe_path in REQUIRED_GITIGNORE_PATTERNS.items():
        if required_pattern not in normalized_patterns:
            error(f".gitignore: missing required ignore pattern '{required_pattern}'")
        result = subprocess.run(
            ["git", "check-ignore", "-q", probe_path],
            cwd=ROOT,
            check=False,
        )
        if result.returncode == 1:
            error(f"{probe_path}: must be ignored by .gitignore")

    broad_patterns = {
        ".agents/",
        ".agents/**",
        ".claude/",
        ".claude/**",
        ".codex/",
        ".codex/**",
    }
    for line_number, line in enumerate(gitignore_lines, start=1):
        stripped = line.strip()
        if stripped in broad_patterns:
            error(f".gitignore:{line_number}: broad agent ignore pattern hides committed docs or skills")

    for skill_path in [
        ".agents/skills/vault_capture/SKILL.md",
        ".claude/skills/vault_capture/SKILL.md",
        ".codex/README.md",
    ]:
        result = subprocess.run(
            ["git", "check-ignore", "-q", skill_path],
            cwd=ROOT,
            check=False,
        )
        if result.returncode == 0:
            error(f"{skill_path}: must not be ignored by .gitignore")


def check_private_folder_tracking() -> None:
    tracked = git_ls_files("--cached")
    if tracked is None:
        return
    for relative in sorted(tracked):
        if any(relative == folder or relative.startswith(f"{folder}/") for folder in PRIVATE_FOLDERS):
            error(f"{relative}: private folder content must not be tracked")


def check_script_structure() -> None:
    validate_wrapper = ROOT / "12_tools/scripts/validate.sh"
    validate_script = ROOT / "12_tools/scripts/validate_vault.py"
    scripts_readme = ROOT / "12_tools/scripts/README.md"

    if not validate_wrapper.exists():
        error("12_tools/scripts/validate.sh is missing")
        return
    if not validate_script.exists():
        error("12_tools/scripts/validate_vault.py is missing")
        return
    if not scripts_readme.exists():
        error("12_tools/scripts/README.md is missing")

    wrapper_text = read_text(validate_wrapper)
    inline_markers = ["python3 - <<", "python - <<", "<<'PY'", '<<"PY"', "<<PY"]
    for marker in inline_markers:
        if marker in wrapper_text:
            error("12_tools/scripts/validate.sh must stay a thin wrapper, not an inline validator")
            break
    if "python3 12_tools/scripts/validate_vault.py" not in wrapper_text:
        error("12_tools/scripts/validate.sh must call 12_tools/scripts/validate_vault.py")

    if scripts_readme.exists():
        readme_text = read_text(scripts_readme)
        for required in ["validate.sh", "validate_vault.py", "list_due_memory.py", "rewrite_wikilinks.py"]:
            if required not in readme_text:
                error(f"12_tools/scripts/README.md must document {required}")


def check_json_files() -> None:
    for path in all_files():
        if path.suffix != ".json":
            continue
        try:
            json.loads(read_text(path))
        except json.JSONDecodeError as exc:
            error(f"{rel(path)}:{exc.lineno}: invalid JSON: {exc.msg}")


def path_matches_default_folder(path: Path, default_folder: str) -> bool:
    return path_matches_route(rel(path), default_folder)


def default_folders_for_type(row: SchemaRow) -> list[str]:
    if row.note_type == "inbox":
        return [row.default_folder, "04_areas/*/inbox/"]
    return [row.default_folder]


def check_markdown_schema(schema_rows: dict[str, SchemaRow]) -> None:
    statuses = {"inbox", "draft", "active", "review", "stable", "done", "archived"}
    confidence_values = {"low", "medium", "high"}
    allowed_types = set(schema_rows)
    templates = {
        row.default_template
        for row in schema_rows.values()
        if row.default_template != "none"
    }

    for template in sorted(templates):
        template_path = ROOT / "11_templates" / template
        if not template_path.exists():
            error(f"11_templates/{template}: template listed in schema table is missing")
            continue

    for row in schema_rows.values():
        if row.default_template == "none":
            continue
        template_path = ROOT / "11_templates" / row.default_template
        if not template_path.exists():
            continue
        parsed = parse_frontmatter(read_text(template_path), template_path)
        if parsed is None:
            error(f"{rel(template_path)}: template listed in schema table is missing YAML frontmatter")
            continue
        data, _body = parsed
        if data.get("type", "") != row.note_type:
            error(
                f"{rel(template_path)}: template type '{data.get('type', '')}' "
                f"does not match schema row type '{row.note_type}'"
            )

    for path in all_files():
        if path.suffix != ".md":
            continue
        text = read_text(path)
        parsed = parse_frontmatter(text, path)
        if parsed is None:
            if not note_schema_exempt(path):
                error(f"{rel(path)}: missing YAML frontmatter")
            continue

        data, _body = parsed
        if note_schema_exempt(path):
            continue

        for required_key in ["type", "status", "created", "updated", "tags"]:
            if required_key not in data:
                error(f"{rel(path)}: missing frontmatter key '{required_key}'")

        note_type = data.get("type", "")
        status = data.get("status", "")
        confidence = data.get("confidence", "")
        review_after = data.get("review_after", "")

        if note_type not in allowed_types:
            error(f"{rel(path)}: type '{note_type}' is not allowed")
        else:
            if not rel(path).startswith("11_templates/") and not default_folder_exempt(path):
                row = schema_rows[note_type]
                allowed_folders = default_folders_for_type(row)
                if not any(path_matches_default_folder(path, folder) for folder in allowed_folders):
                    folder_list = " or ".join(f"'{folder}'" for folder in allowed_folders)
                    error(
                        f"{rel(path)}: type '{note_type}' belongs under "
                        f"{folder_list}"
                    )
        if status not in statuses:
            error(f"{rel(path)}: status '{status}' is not allowed")
        if confidence and confidence not in confidence_values:
            error(f"{rel(path)}: confidence '{confidence}' is not allowed")
        if review_after and not is_iso_date(review_after):
            error(f"{rel(path)}: review_after '{review_after}' is not YYYY-MM-DD")
        for date_key in ["created", "updated"]:
            date_value = data.get(date_key, "")
            if date_value and not is_iso_date_or_datetime(date_value):
                error(f"{rel(path)}: {date_key} '{date_value}' is not YYYY-MM-DD or ISO 8601 datetime")


def slugify_heading(heading: str) -> str:
    heading = heading.strip().strip("#").strip().lower()
    heading = re.sub(r"[^\w\s-]", "", heading)
    heading = re.sub(r"\s+", "-", heading)
    heading = re.sub(r"-+", "-", heading)
    return heading


def build_link_index() -> tuple[
    dict[str, Path],
    dict[str, list[Path]],
    dict[str, set[str]],
    dict[str, set[str]],
    dict[str, Path],
    dict[str, list[Path]],
]:
    by_path: dict[str, Path] = {}
    by_name: dict[str, list[Path]] = {}
    headings: dict[str, set[str]] = {}
    blocks: dict[str, set[str]] = {}
    files_by_path: dict[str, Path] = {}
    files_by_name: dict[str, list[Path]] = {}

    for path in all_files():
        files_by_path[rel(path)] = path
        files_by_name.setdefault(path.name, []).append(path)

        if path.suffix != ".md":
            continue
        relative_no_suffix = rel(path.with_suffix(""))
        by_path[relative_no_suffix] = path
        by_name.setdefault(path.stem, []).append(path)

        text = read_text(path)
        path_headings: set[str] = set()
        path_blocks: set[str] = set()
        for _line_number, line in iter_non_fenced_lines(text):
            heading_match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
            if heading_match:
                path_headings.add(slugify_heading(heading_match.group(2)))
            block_match = re.search(r"(?:^|\s)\^([A-Za-z0-9_-]+)\s*$", line)
            if block_match:
                path_blocks.add(block_match.group(1))
        headings[rel(path)] = path_headings
        blocks[rel(path)] = path_blocks

    return by_path, by_name, headings, blocks, files_by_path, files_by_name


def resolve_wikilink_target(target: str, source: Path, by_path: dict[str, Path], by_name: dict[str, list[Path]]) -> Path | None:
    if not target:
        return source
    normalized = target.removesuffix(".md").strip("/")
    if normalized in by_path:
        return by_path[normalized]
    if normalized in by_name:
        matches = by_name[normalized]
        if len(matches) == 1:
            return matches[0]
        error(f"{rel(source)}: wikilink target '{target}' is ambiguous")
        return None
    return None


def resolve_file_embed_target(
    target: str,
    source: Path,
    files_by_path: dict[str, Path],
    files_by_name: dict[str, list[Path]],
) -> Path | None:
    normalized = target.strip("/")
    if normalized in files_by_path:
        return files_by_path[normalized]
    if "/" not in normalized and normalized in files_by_name:
        matches = files_by_name[normalized]
        if len(matches) == 1:
            return matches[0]
        error(f"{rel(source)}: file embed target '{target}' is ambiguous")
    return None


def check_wikilinks() -> None:
    by_path, by_name, headings, blocks, files_by_path, files_by_name = build_link_index()
    pattern = re.compile(r"\[\[([^\]]+)\]\]")

    for path in all_files():
        if path.suffix != ".md":
            continue
        if rel(path).startswith("_prompts/"):
            continue
        text = text_without_fenced_blocks(read_text(path))
        for match in pattern.finditer(text):
            is_embed = match.start() > 0 and text[match.start() - 1] == "!"
            raw_target = match.group(1).split("|", 1)[0].strip()
            note_part = raw_target
            fragment = ""
            if "#" in raw_target:
                note_part, fragment = raw_target.split("#", 1)
            target_path = resolve_wikilink_target(note_part, path, by_path, by_name)
            if target_path is None and is_embed:
                target_path = resolve_file_embed_target(note_part, path, files_by_path, files_by_name)
            if target_path is None:
                error(f"{rel(path)}: broken wikilink '{match.group(0)}'")
                continue
            target_relative = rel(target_path)
            if fragment.startswith("^"):
                block_id = fragment[1:]
                if block_id and block_id not in blocks.get(target_relative, set()):
                    error(f"{rel(path)}: wikilink block '{match.group(0)}' does not exist")
            elif fragment:
                slug = slugify_heading(fragment)
                if slug not in headings.get(target_relative, set()):
                    error(f"{rel(path)}: wikilink heading '{match.group(0)}' does not exist")


def check_memory_metadata() -> None:
    due_pattern = re.compile(r"^\s*due::\s*(.*)\s*$")
    state_pattern = re.compile(r"^\s*state::\s*(.*)\s*$")
    states = {"new", "learning", "review", "suspended"}

    for path in all_files():
        if path.suffix != ".md":
            continue
        if rel(path).startswith("_prompts/"):
            continue
        for line_number, line in iter_non_fenced_lines(read_text(path)):
            due_match = due_pattern.match(line)
            if due_match:
                value = due_match.group(1).strip()
                if value and not is_iso_date(value):
                    error(f"{rel(path)}:{line_number}: due:: '{value}' is not YYYY-MM-DD")
            state_match = state_pattern.match(line)
            if state_match:
                value = state_match.group(1).strip()
                if value and value not in states:
                    error(f"{rel(path)}:{line_number}: state:: '{value}' is not allowed")


def filename_convention_exempt(path: Path) -> bool:
    relative = rel(path)
    if path.name == "README.md":
        return True
    if relative in {"AGENTS.md", "CLAUDE.md", "LICENSE", "README.md"}:
        return True
    if relative.startswith(("00_system/", "02_journal/", "10_agents/", "11_templates/", "12_tools/", "_prompts/")):
        return True
    if relative.startswith((".agents/", ".claude/", ".codex/", ".github/", ".obsidian/")):
        return True
    return False


def requires_timestamped_filename(path: Path) -> bool:
    if filename_convention_exempt(path):
        return False

    relative = rel(path)
    parts = path.relative_to(ROOT).parts
    if len(parts) >= 3 and parts[0] == "04_areas":
        return True
    if path.suffix == ".md" and relative.startswith("01_inbox/"):
        return True
    return False


def filename_stem(path: Path) -> str:
    if "." not in path.name:
        return path.name
    return path.name.rsplit(".", 1)[0]


def check_filename_conventions() -> None:
    for path in all_files():
        if not requires_timestamped_filename(path):
            continue
        if not TIMESTAMPED_NAME_PATTERN.fullmatch(filename_stem(path)):
            error(
                f"{rel(path)}: filename must match "
                "YYYY-MM-DDTHHMMSS+HHMM_2-to-4-word-slug"
            )


def check_secrets_and_local_paths() -> None:
    secret_patterns = [
        ("OpenAI-style API key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
        ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
        ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
        ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
        ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
        (
            "credential assignment",
            re.compile(
                r"(?i)\b(oauth[_-]?token|access[_-]?token|refresh[_-]?token|api[_-]?key|client[_-]?secret)\b\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}"
            ),
        ),
    ]
    local_path_patterns = [
        re.compile(r"(?<![A-Za-z0-9_])/(?:Users|home)/[A-Za-z0-9._-]+"),
        re.compile(r"\b[A-Za-z]:\\Users\\[A-Za-z0-9._-]+"),
    ]

    for path in all_files():
        relative = rel(path)
        text = read_scan_text(path)
        for label, pattern in secret_patterns:
            if pattern.search(text):
                error(f"{relative}: possible secret detected: {label}")
        for pattern in local_path_patterns:
            if pattern.search(text):
                error(f"{relative}: possible local absolute path detected")


def check_large_files() -> None:
    lfs_files: set[str] = set()
    result = subprocess.run(
        ["git", "lfs", "ls-files", "-n"],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        lfs_files = {line.strip() for line in result.stdout.splitlines() if line.strip()}

    warn_threshold = 5 * 1024 * 1024
    block_threshold = 25 * 1024 * 1024

    for path in all_files():
        relative = rel(path)
        size = path.stat().st_size
        if size > block_threshold and relative not in lfs_files:
            error(f"{relative}: file is above 25 MB and is not tracked by Git LFS")
        elif size > warn_threshold and relative not in lfs_files:
            warn(f"{relative}: file is above 5 MB")


def check_skills() -> None:
    skill_names = {
        "vault_capture",
        "vault_triage",
        "vault_search",
        "vault_summarize",
        "vault_synthesize",
        "vault_memory_update",
    }
    for root in [".agents/skills", ".claude/skills"]:
        for name in sorted(skill_names):
            path = ROOT / root / name / "SKILL.md"
            if not path.exists():
                error(f"{root}/{name}/SKILL.md: missing skill file")
                continue
            text = read_text(path)
            lower = text.lower()
            for heading in ["allowed reads", "allowed writes", "forbidden paths", "approval requirements"]:
                if f"## {heading}" not in lower:
                    error(f"{rel(path)}: missing '{heading}' section")
            if re.search(r"```(?:bash|sh|shell)", lower):
                error(f"{rel(path)}: skill contains an auto-running shell-style snippet")
            if name == "vault_search" and "## allowed writes\n\nnone." not in lower:
                error(f"{rel(path)}: vault_search must document no write access")
            if name == "vault_capture":
                for allowed in ["01_inbox/quick_notes/", "01_inbox/agent_inbox/", "04_areas/*/inbox/"]:
                    if allowed not in text:
                        error(f"{rel(path)}: vault_capture missing allowed write scope {allowed}")
            if name == "vault_triage" and "rewrite_wikilinks.py" not in text:
                error(f"{rel(path)}: vault_triage must document wikilink rewriting")
            if name == "vault_summarize":
                for allowed in ["01_inbox/agent_inbox/", "04_areas/*/outputs/"]:
                    if allowed not in text:
                        error(f"{rel(path)}: vault_summarize missing allowed write scope {allowed}")
            if name == "vault_synthesize":
                for allowed in ["01_inbox/agent_inbox/", "04_areas/*/notes/synthesis/"]:
                    if allowed not in text:
                        error(f"{rel(path)}: vault_synthesize missing allowed write scope {allowed}")
            if name == "vault_memory_update" and "10_agents/memory/candidates/" not in text:
                error(f"{rel(path)}: vault_memory_update missing candidate write scope")


def check_markdown_style_basics() -> None:
    for path in all_files():
        if path.suffix not in {".md", ".yaml", ".yml", ".json", ".sh", ".py", ".txt"}:
            continue
        text = read_text(path)
        if text and not text.endswith("\n"):
            error(f"{rel(path)}: missing final newline")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.rstrip(" \t") != line:
                error(f"{rel(path)}:{line_number}: trailing whitespace")


def run_checks(root: str | Path) -> ValidationResult:
    reset_context(root)
    paths = all_paths()
    schema_rows = parse_schema()

    check_paths(paths)
    check_gitignore()
    check_private_folder_tracking()
    check_script_structure()
    check_json_files()
    check_markdown_schema(schema_rows)
    check_wikilinks()
    check_memory_metadata()
    check_filename_conventions()
    check_secrets_and_local_paths()
    check_large_files()
    check_skills()
    check_markdown_style_basics()

    return ValidationResult(errors=list(ERRORS), warnings=list(WARNINGS))


def main() -> int:
    result = run_checks(Path.cwd())

    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)

    if result.errors:
        print("Validation failed:", file=sys.stderr)
        for item in result.errors:
            print(f"- {item}", file=sys.stderr)
        return 1

    print("Core vault validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
