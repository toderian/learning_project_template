from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path("12_tools") / "scripts"
VALIDATOR_PATH = REPO_ROOT / SCRIPTS_DIR / "validate_vault.py"
NOTE_TIMESTAMP = "2026-06-09T14:30:12+03:00"
NOTE_STEM = "2026-06-09T143012+0300"

spec = importlib.util.spec_from_file_location("validate_vault_under_test", VALIDATOR_PATH)
assert spec is not None
assert spec.loader is not None
validator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


@pytest.fixture()
def vault_root(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    root.mkdir()

    repo_files = run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], REPO_ROOT).stdout
    for relative in sorted(item for item in repo_files.split("\0") if item):
        source = REPO_ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    run(["git", "init"], root)
    run(["git", "add", "-A"], root)
    return root


def validate(root: Path):
    return validator.run_checks(root)


def run_cli(root: Path, script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, (SCRIPTS_DIR / script).as_posix(), *args],
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def assert_valid(root: Path) -> None:
    result = validate(root)
    assert result.errors == []


def assert_has_error(root: Path, expected: str) -> None:
    result = validate(root)
    assert any(expected in error for error in result.errors), result.errors


def note_text(
    note_type: str,
    title: str,
    body: str = "",
    extra_frontmatter: str = "",
) -> str:
    extra = f"{extra_frontmatter}\n" if extra_frontmatter else ""
    return (
        "---\n"
        f"type: {note_type}\n"
        "status: inbox\n"
        f"created: {NOTE_TIMESTAMP}\n"
        f"updated: {NOTE_TIMESTAMP}\n"
        "tags: []\n"
        f"{extra}"
        "---\n"
        "\n"
        f"# {title}\n"
        "\n"
        f"{body}\n"
    )


def write_note(
    root: Path,
    relative: str,
    note_type: str,
    title: str = "Fixture Note",
    body: str = "",
    extra_frontmatter: str = "",
) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        note_text(note_type, title, body=body, extra_frontmatter=extra_frontmatter),
        encoding="utf-8",
    )
    return path


def test_baseline_temp_vault_passes_validation(vault_root: Path) -> None:
    assert_valid(vault_root)


def test_cli_success_output_and_exit_code_are_preserved(vault_root: Path) -> None:
    result = subprocess.run(
        [sys.executable, "12_tools/scripts/validate_vault.py"],
        cwd=vault_root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0
    assert result.stdout == "Core vault validation passed.\n"
    assert result.stderr == ""


def test_create_area_cli_creates_expected_readme_and_skeleton(vault_root: Path) -> None:
    result = run_cli(
        vault_root,
        "create_area.py",
        "web-security",
        "--timestamp",
        NOTE_TIMESTAMP,
    )

    assert result.returncode == 0
    assert result.stdout == "Created 04_areas/web-security/README.md\n"
    assert result.stderr == ""

    readme = vault_root / "04_areas/web-security/README.md"
    assert readme.is_file()
    assert (vault_root / "04_areas/web-security/notes/atomic").is_dir()
    assert (vault_root / "04_areas/web-security/assets/images").is_dir()
    assert "created: 2026-06-09T14:30:12+03:00" in readme.read_text(encoding="utf-8")
    assert "# Web Security" in readme.read_text(encoding="utf-8")
    assert_valid(vault_root)


def test_create_area_cli_refuses_existing_area(vault_root: Path) -> None:
    first = run_cli(vault_root, "create_area.py", "web-security", "--timestamp", NOTE_TIMESTAMP)
    second = run_cli(vault_root, "create_area.py", "web-security", "--timestamp", NOTE_TIMESTAMP)

    assert first.returncode == 0
    assert second.returncode == 2
    assert "area already exists" in second.stderr


def test_create_area_cli_invalid_area_slug_fails_nonzero(vault_root: Path) -> None:
    result = run_cli(vault_root, "create_area.py", "WebSecurity", "--timestamp", NOTE_TIMESTAMP)

    assert result.returncode == 2
    assert "AREA must be lowercase kebab-case" in result.stderr


def test_new_note_cli_creates_valid_area_atomic_note(vault_root: Path) -> None:
    run_cli(vault_root, "create_area.py", "web-security", "--timestamp", NOTE_TIMESTAMP)
    result = run_cli(
        vault_root,
        "new_note.py",
        "atomic",
        "SQL injection basics",
        "--area",
        "web-security",
        "--timestamp",
        NOTE_TIMESTAMP,
    )

    target = vault_root / f"04_areas/web-security/notes/atomic/{NOTE_STEM}_sql-injection-basics.md"
    assert result.returncode == 0
    assert result.stdout == f"Created {target.relative_to(vault_root).as_posix()}\n"
    assert target.is_file()
    text = target.read_text(encoding="utf-8")
    assert "type: atomic" in text
    assert "created: 2026-06-09T14:30:12+03:00" in text
    assert "# SQL injection basics" in text
    assert_valid(vault_root)


def test_new_note_cli_creates_valid_global_and_area_inbox_notes(vault_root: Path) -> None:
    run_cli(vault_root, "create_area.py", "web-security", "--timestamp", NOTE_TIMESTAMP)

    global_result = run_cli(
        vault_root,
        "new_note.py",
        "inbox",
        "Untyped capture",
        "--timestamp",
        NOTE_TIMESTAMP,
    )
    area_result = run_cli(
        vault_root,
        "new_note.py",
        "inbox",
        "Known capture",
        "--area",
        "web-security",
        "--timestamp",
        NOTE_TIMESTAMP,
    )

    assert global_result.returncode == 0
    assert area_result.returncode == 0
    assert (vault_root / f"01_inbox/quick_notes/{NOTE_STEM}_untyped-capture.md").is_file()
    assert (vault_root / f"04_areas/web-security/inbox/{NOTE_STEM}_known-capture.md").is_file()
    assert_valid(vault_root)


def test_new_note_cli_creates_valid_global_agent_draft(vault_root: Path) -> None:
    result = run_cli(
        vault_root,
        "new_note.py",
        "agent_draft",
        "Draft synthesis",
        "--timestamp",
        NOTE_TIMESTAMP,
    )

    target = vault_root / f"01_inbox/agent_inbox/{NOTE_STEM}_draft-synthesis.md"
    assert result.returncode == 0
    assert target.is_file()
    assert "type: agent_draft" in target.read_text(encoding="utf-8")
    assert_valid(vault_root)


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (("atomic", "SQL injection basics", "--area", "missing-area"), "area 'missing-area' does not exist"),
        (("atomic", "SQL injection basics", "--area", "WebSecurity"), "AREA must be lowercase kebab-case"),
        (("atomic", "SQL injection basics", "--area", "web-security", "--slug", "bad"), "slug must be 2 to 4"),
        (("area", "Web Security"), "type 'area' is created with create_area.py"),
        (("tool", "Local Tool"), "type 'tool' is not supported"),
    ],
)
def test_new_note_cli_invalid_inputs_fail_nonzero(
    vault_root: Path,
    args: tuple[str, ...],
    expected: str,
) -> None:
    run_cli(vault_root, "create_area.py", "web-security", "--timestamp", NOTE_TIMESTAMP)

    result = run_cli(vault_root, "new_note.py", *args, "--timestamp", NOTE_TIMESTAMP)

    assert result.returncode == 2
    assert expected in result.stderr


def test_creation_clis_require_timezone_aware_timestamp(vault_root: Path) -> None:
    area_result = run_cli(vault_root, "create_area.py", "web-security", "--timestamp", "2026-06-09T14:30:12")
    note_result = run_cli(vault_root, "new_note.py", "inbox", "Untyped capture", "--timestamp", "2026-06-09T14:30:12")

    assert area_result.returncode == 2
    assert note_result.returncode == 2
    assert "--timestamp must include a timezone offset" in area_result.stderr
    assert "--timestamp must include a timezone offset" in note_result.stderr


def test_new_note_cli_missing_template_fails_nonzero(vault_root: Path) -> None:
    run_cli(vault_root, "create_area.py", "web-security", "--timestamp", NOTE_TIMESTAMP)
    (vault_root / "11_templates/atomic_note.md").unlink()

    result = run_cli(
        vault_root,
        "new_note.py",
        "atomic",
        "SQL injection basics",
        "--area",
        "web-security",
        "--timestamp",
        NOTE_TIMESTAMP,
    )

    assert result.returncode == 2
    assert "11_templates/atomic_note.md is missing" in result.stderr


def test_new_note_cli_duplicate_target_fails_nonzero(vault_root: Path) -> None:
    run_cli(vault_root, "create_area.py", "web-security", "--timestamp", NOTE_TIMESTAMP)
    first = run_cli(
        vault_root,
        "new_note.py",
        "atomic",
        "SQL injection basics",
        "--area",
        "web-security",
        "--timestamp",
        NOTE_TIMESTAMP,
    )
    second = run_cli(
        vault_root,
        "new_note.py",
        "atomic",
        "SQL injection basics",
        "--area",
        "web-security",
        "--timestamp",
        NOTE_TIMESTAMP,
    )

    assert first.returncode == 0
    assert second.returncode == 2
    assert "target already exists" in second.stderr


def test_inbox_type_is_valid_in_global_and_area_local_routes(vault_root: Path) -> None:
    write_note(
        vault_root,
        f"01_inbox/quick_notes/{NOTE_STEM}_untyped-capture.md",
        "inbox",
        title="Untyped Capture",
    )
    write_note(
        vault_root,
        f"04_areas/web-security/inbox/{NOTE_STEM}_known-capture.md",
        "inbox",
        title="Known Capture",
    )

    assert_valid(vault_root)


def test_old_global_routes_fail_validation(vault_root: Path) -> None:
    write_note(
        vault_root,
        f"03_projects/{NOTE_STEM}_legacy-project-note.md",
        "project",
        title="Legacy Project Note",
    )

    assert_has_error(vault_root, "removed global topic layer")


def test_non_timestamped_area_notes_fail_validation(vault_root: Path) -> None:
    write_note(
        vault_root,
        "04_areas/web-security/notes/atomic/sql-injection-basics.md",
        "atomic",
        title="SQL Injection Basics",
    )

    assert_has_error(vault_root, "filename must match")


def test_review_after_datetime_fails_but_date_only_passes(vault_root: Path) -> None:
    write_note(
        vault_root,
        f"04_areas/web-security/notes/atomic/{NOTE_STEM}_date-only-review.md",
        "atomic",
        title="Date Only Review",
        extra_frontmatter="review_after: 2026-06-10",
    )
    assert_valid(vault_root)

    write_note(
        vault_root,
        f"04_areas/web-security/notes/atomic/{NOTE_STEM}_datetime-review.md",
        "atomic",
        title="Datetime Review",
        extra_frontmatter="review_after: 2026-06-10T12:00:00+03:00",
    )

    assert_has_error(vault_root, "review_after '2026-06-10T12:00:00+03:00' is not YYYY-MM-DD")


def test_valid_area_asset_embed_passes_and_broken_embed_fails(vault_root: Path) -> None:
    asset = vault_root / f"04_areas/web-security/assets/images/network-scanning/{NOTE_STEM}_nmap-scan-output.png"
    asset.parent.mkdir(parents=True, exist_ok=True)
    asset.write_bytes(b"\x89PNG\r\n\x1a\n")
    write_note(
        vault_root,
        f"04_areas/web-security/notes/atomic/{NOTE_STEM}_asset-embed-note.md",
        "atomic",
        title="Asset Embed Note",
        body=f"![[04_areas/web-security/assets/images/network-scanning/{NOTE_STEM}_nmap-scan-output.png]]",
    )
    assert_valid(vault_root)

    write_note(
        vault_root,
        f"04_areas/web-security/notes/atomic/{NOTE_STEM}_broken-embed-note.md",
        "atomic",
        title="Broken Embed Note",
        body="![[04_areas/web-security/assets/missing-output.png]]",
    )

    assert_has_error(vault_root, "broken wikilink")


def test_curated_assets_require_category_and_topic_folder(vault_root: Path) -> None:
    direct_asset = vault_root / f"04_areas/web-security/assets/images/{NOTE_STEM}_direct-image.png"
    direct_asset.parent.mkdir(parents=True, exist_ok=True)
    direct_asset.write_bytes(b"\x89PNG\r\n\x1a\n")

    assert_has_error(vault_root, "curated assets must live under")


def test_curated_asset_topic_folders_must_be_kebab_case(vault_root: Path) -> None:
    asset = vault_root / f"04_areas/web-security/assets/images/Network Scanning/{NOTE_STEM}_nmap-scan-output.png"
    asset.parent.mkdir(parents=True, exist_ok=True)
    asset.write_bytes(b"\x89PNG\r\n\x1a\n")

    assert_has_error(vault_root, "must be lowercase kebab-case")


@pytest.mark.parametrize("private_folder", [".creds", ".no-commit"])
def test_tracked_private_folder_content_fails(vault_root: Path, private_folder: str) -> None:
    private_file = vault_root / private_folder / "local.txt"
    private_file.parent.mkdir(parents=True, exist_ok=True)
    private_file.write_text("local scratch\n", encoding="utf-8")
    run(["git", "add", "-f", private_file.relative_to(vault_root).as_posix()], vault_root)

    assert_has_error(vault_root, "private folder content must not be tracked")


@pytest.mark.parametrize("missing_pattern", [".creds/", ".no-commit/", ".env", ".env.*"])
def test_missing_private_ignore_rules_fail_validation(
    vault_root: Path,
    missing_pattern: str,
) -> None:
    gitignore = vault_root / ".gitignore"
    lines = [
        line
        for line in gitignore.read_text(encoding="utf-8").splitlines()
        if line.strip() != missing_pattern
    ]
    gitignore.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assert_has_error(vault_root, f"missing required ignore pattern '{missing_pattern}'")


@pytest.mark.parametrize("pattern", ["!.creds/allowed.txt", "!.no-commit/**"])
def test_private_folder_unignore_patterns_fail_validation(
    vault_root: Path,
    pattern: str,
) -> None:
    gitignore = vault_root / ".gitignore"
    with gitignore.open("a", encoding="utf-8") as handle:
        handle.write(f"{pattern}\n")

    assert_has_error(vault_root, "private folder unignore pattern is forbidden")
