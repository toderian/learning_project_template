from __future__ import annotations

import importlib.util
import os
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
FAKE_OPENAI_KEY = "sk-" + "1234567890abcdefghijklmnop"

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


def create_test_area(root: Path, area: str = "web-security") -> None:
    result = run_cli(root, "create_area.py", area, "--timestamp", NOTE_TIMESTAMP)
    assert result.returncode == 0, result.stderr


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
    create_test_area(vault_root)
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


def test_area_folder_names_must_be_lowercase_kebab_case(vault_root: Path) -> None:
    write_note(
        vault_root,
        f"04_areas/WebSecurity/notes/atomic/{NOTE_STEM}_invalid-area-slug.md",
        "atomic",
        title="Invalid Area Slug",
    )

    assert_has_error(vault_root, "area folder must be lowercase kebab-case")


def test_area_content_requires_readme_marker(vault_root: Path) -> None:
    write_note(
        vault_root,
        f"04_areas/web-security/notes/atomic/{NOTE_STEM}_missing-area-marker.md",
        "atomic",
        title="Missing Area Marker",
    )

    assert_has_error(vault_root, "area README marker is missing")


def test_area_readme_marker_requires_valid_frontmatter(vault_root: Path) -> None:
    area_readme = vault_root / "04_areas/web-security/README.md"
    area_readme.parent.mkdir(parents=True, exist_ok=True)
    area_readme.write_text("# Web Security\n", encoding="utf-8")

    assert_has_error(vault_root, "area README marker is missing YAML frontmatter")


def test_area_readme_marker_type_must_be_area(vault_root: Path) -> None:
    area_readme = vault_root / "04_areas/web-security/README.md"
    area_readme.parent.mkdir(parents=True, exist_ok=True)
    area_readme.write_text(
        note_text("atomic", "Web Security"),
        encoding="utf-8",
    )

    assert_has_error(vault_root, "area README marker type must be 'area'")


def test_old_global_routes_fail_validation(vault_root: Path) -> None:
    write_note(
        vault_root,
        f"03_projects/{NOTE_STEM}_legacy-project-note.md",
        "project",
        title="Legacy Project Note",
    )

    assert_has_error(vault_root, "removed global topic layer")


def test_non_timestamped_area_notes_fail_validation(vault_root: Path) -> None:
    create_test_area(vault_root)
    write_note(
        vault_root,
        "04_areas/web-security/notes/atomic/sql-injection-basics.md",
        "atomic",
        title="SQL Injection Basics",
    )

    assert_has_error(vault_root, "filename must match")


def test_review_after_datetime_fails_but_date_only_passes(vault_root: Path) -> None:
    create_test_area(vault_root)
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
    create_test_area(vault_root)
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
    create_test_area(vault_root)
    direct_asset = vault_root / f"04_areas/web-security/assets/images/{NOTE_STEM}_direct-image.png"
    direct_asset.parent.mkdir(parents=True, exist_ok=True)
    direct_asset.write_bytes(b"\x89PNG\r\n\x1a\n")

    assert_has_error(vault_root, "curated assets must live under")


def test_curated_asset_topic_folders_must_be_kebab_case(vault_root: Path) -> None:
    create_test_area(vault_root)
    asset = vault_root / f"04_areas/web-security/assets/images/Network Scanning/{NOTE_STEM}_nmap-scan-output.png"
    asset.parent.mkdir(parents=True, exist_ok=True)
    asset.write_bytes(b"\x89PNG\r\n\x1a\n")

    assert_has_error(vault_root, "must be lowercase kebab-case")


def test_curated_asset_category_folders_must_be_supported(vault_root: Path) -> None:
    create_test_area(vault_root)
    asset = vault_root / f"04_areas/web-security/assets/photos/network-scanning/{NOTE_STEM}_nmap-scan-output.png"
    asset.parent.mkdir(parents=True, exist_ok=True)
    asset.write_bytes(b"\x89PNG\r\n\x1a\n")

    assert_has_error(vault_root, "asset category must be one of")


def test_curated_assets_require_supported_lowercase_extensions(vault_root: Path) -> None:
    create_test_area(vault_root)
    extensionless = vault_root / f"04_areas/web-security/assets/images/network-scanning/{NOTE_STEM}_scan-output"
    uppercase = vault_root / f"04_areas/web-security/assets/images/network-scanning/{NOTE_STEM}_scan-output.PNG"
    wrong_category = vault_root / f"04_areas/web-security/assets/images/network-scanning/{NOTE_STEM}_lab-notes.pdf"
    for asset in [extensionless, uppercase, wrong_category]:
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(b"asset\n")

    result = validate(vault_root)

    assert any("asset must have a lowercase supported file extension" in error for error in result.errors)
    assert any("asset extension must be lowercase" in error for error in result.errors)
    assert any("asset extension '.pdf' is not supported for images" in error for error in result.errors)


def test_curated_assets_over_five_mb_require_lfs(vault_root: Path) -> None:
    create_test_area(vault_root)
    asset = vault_root / f"04_areas/web-security/assets/images/network-scanning/{NOTE_STEM}_large-capture.png"
    asset.parent.mkdir(parents=True, exist_ok=True)
    asset.write_bytes(b"0" * (5 * 1024 * 1024 + 1))

    assert_has_error(vault_root, "curated asset is above 5 MB and is not tracked by Git LFS")


def test_non_asset_over_five_mb_warns_without_failing(vault_root: Path) -> None:
    large_file = vault_root / "01_inbox/raw_files/large-export.bin"
    large_file.write_bytes(b"0" * (5 * 1024 * 1024 + 1))

    result = validate(vault_root)

    assert result.errors == []
    assert any("file is above 5 MB" in warning for warning in result.warnings)


def test_new_asset_cli_moves_image_to_expected_path(vault_root: Path) -> None:
    run_cli(vault_root, "create_area.py", "web-security", "--timestamp", NOTE_TIMESTAMP)
    source = vault_root / "source-scan.png"
    source.write_bytes(b"\x89PNG\r\n\x1a\n")

    result = run_cli(
        vault_root,
        "new_asset.py",
        "image",
        source.as_posix(),
        "--area",
        "web-security",
        "--topic",
        "network-scanning",
        "--title",
        "Nmap scan output",
        "--timestamp",
        NOTE_TIMESTAMP,
    )

    target = vault_root / f"04_areas/web-security/assets/images/network-scanning/{NOTE_STEM}_nmap-scan-output.png"
    assert result.returncode == 0
    assert result.stdout == f"Created {target.relative_to(vault_root).as_posix()}\n"
    assert result.stderr == ""
    assert target.read_bytes() == b"\x89PNG\r\n\x1a\n"
    assert not source.exists()
    assert_valid(vault_root)


def test_new_asset_cli_copy_mode_leaves_source_in_place(vault_root: Path) -> None:
    run_cli(vault_root, "create_area.py", "web-security", "--timestamp", NOTE_TIMESTAMP)
    source = vault_root / "lab-notes.pdf"
    source.write_bytes(b"%PDF-1.7\n")

    result = run_cli(
        vault_root,
        "new_asset.py",
        "pdf",
        source.as_posix(),
        "--area",
        "web-security",
        "--topic",
        "sql-injection",
        "--title",
        "Lab notes",
        "--timestamp",
        NOTE_TIMESTAMP,
        "--copy",
    )

    target = vault_root / f"04_areas/web-security/assets/attachments/sql-injection/{NOTE_STEM}_lab-notes.pdf"
    assert result.returncode == 0
    assert target.read_bytes() == b"%PDF-1.7\n"
    assert source.read_bytes() == b"%PDF-1.7\n"
    assert_valid(vault_root)


def test_new_asset_cli_dry_run_does_not_write_or_move(vault_root: Path) -> None:
    run_cli(vault_root, "create_area.py", "web-security", "--timestamp", NOTE_TIMESTAMP)
    source = vault_root / "exported-chat.json"
    source.write_bytes(b'{"ok": true}\n')

    result = run_cli(
        vault_root,
        "new_asset.py",
        "import",
        source.as_posix(),
        "--area",
        "web-security",
        "--topic",
        "chatgpt-exports",
        "--title",
        "Exported chat",
        "--timestamp",
        NOTE_TIMESTAMP,
        "--dry-run",
    )

    target = vault_root / f"04_areas/web-security/assets/imports/chatgpt-exports/{NOTE_STEM}_exported-chat.json"
    assert result.returncode == 0
    assert f"Source: {source}\n" in result.stdout
    assert "Action: move\n" in result.stdout
    assert f"Target: {target.relative_to(vault_root).as_posix()}\n" in result.stdout
    assert f"Would create {target.relative_to(vault_root).as_posix()}\n" in result.stdout
    assert source.is_file()
    assert not target.exists()


def test_new_asset_cli_accepts_nested_topic_path(vault_root: Path) -> None:
    run_cli(vault_root, "create_area.py", "web-security", "--timestamp", NOTE_TIMESTAMP)
    source = vault_root / "login-form.jpeg"
    source.write_bytes(b"\xff\xd8\xff")

    result = run_cli(
        vault_root,
        "new_asset.py",
        "screenshot",
        source.as_posix(),
        "--area",
        "web-security",
        "--topic",
        "sql-injection/login-forms",
        "--title",
        "Login form",
        "--timestamp",
        NOTE_TIMESTAMP,
    )

    target = vault_root / f"04_areas/web-security/assets/images/sql-injection/login-forms/{NOTE_STEM}_login-form.jpeg"
    assert result.returncode == 0
    assert target.is_file()
    assert_valid(vault_root)


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (
            ("image", "source-scan.png", "--area", "missing-area", "--topic", "network-scanning"),
            "area 'missing-area' does not exist",
        ),
        (
            ("image", "source-scan.png", "--area", "web-security", "--topic", "Network Scanning"),
            "--topic must be a slash-separated lowercase kebab-case path",
        ),
        (
            ("photos", "source-scan.png", "--area", "web-security", "--topic", "network-scanning"),
            "CATEGORY must be one of",
        ),
        (
            ("image", "missing.png", "--area", "web-security", "--topic", "network-scanning"),
            "source file does not exist",
        ),
        (
            ("image", "source-dir", "--area", "web-security", "--topic", "network-scanning"),
            "SOURCE must be a file, not a directory",
        ),
        (
            ("image", "source-scan", "--area", "web-security", "--topic", "network-scanning"),
            "SOURCE must have a file extension",
        ),
        (
            ("image", "source-scan.PNG", "--area", "web-security", "--topic", "network-scanning"),
            "asset extension must be lowercase",
        ),
        (
            ("image", "lab-notes.pdf", "--area", "web-security", "--topic", "network-scanning"),
            "asset extension '.pdf' is not supported for images",
        ),
        (
            ("pdf", "source-scan.png", "--area", "web-security", "--topic", "network-scanning"),
            "asset extension '.png' is not supported for attachments",
        ),
        (
            (
                "image",
                "source-scan.png",
                "--area",
                "web-security",
                "--topic",
                "network-scanning",
                "--timestamp",
                "2026-06-09T14:30:12",
            ),
            "--timestamp must include a timezone offset",
        ),
        (
            ("image", "oneword.png", "--area", "web-security", "--topic", "network-scanning"),
            "could not derive a 2 to 4 word slug from source filename",
        ),
    ],
)
def test_new_asset_cli_invalid_inputs_fail_nonzero(
    vault_root: Path,
    args: tuple[str, ...],
    expected: str,
) -> None:
    run_cli(vault_root, "create_area.py", "web-security", "--timestamp", NOTE_TIMESTAMP)
    (vault_root / "source-scan.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (vault_root / "source-scan.PNG").write_bytes(b"\x89PNG\r\n\x1a\n")
    (vault_root / "lab-notes.pdf").write_bytes(b"%PDF-1.7\n")
    (vault_root / "oneword.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (vault_root / "source-scan").write_text("extensionless\n", encoding="utf-8")
    (vault_root / "source-dir").mkdir()

    cli_args = list(args)
    if "--timestamp" not in args:
        cli_args.extend(["--timestamp", NOTE_TIMESTAMP])
    result = run_cli(vault_root, "new_asset.py", *cli_args)

    assert result.returncode == 2
    assert expected in result.stderr


def test_new_asset_cli_duplicate_target_fails_nonzero(vault_root: Path) -> None:
    run_cli(vault_root, "create_area.py", "web-security", "--timestamp", NOTE_TIMESTAMP)
    first_source = vault_root / "first-source.png"
    second_source = vault_root / "second-source.png"
    first_source.write_bytes(b"first\n")
    second_source.write_bytes(b"second\n")

    first = run_cli(
        vault_root,
        "new_asset.py",
        "image",
        first_source.as_posix(),
        "--area",
        "web-security",
        "--topic",
        "network-scanning",
        "--title",
        "Nmap scan output",
        "--timestamp",
        NOTE_TIMESTAMP,
    )
    second = run_cli(
        vault_root,
        "new_asset.py",
        "image",
        second_source.as_posix(),
        "--area",
        "web-security",
        "--topic",
        "network-scanning",
        "--title",
        "Nmap scan output",
        "--timestamp",
        NOTE_TIMESTAMP,
    )

    assert first.returncode == 0
    assert second.returncode == 2
    assert "target already exists" in second.stderr
    assert second_source.is_file()


@pytest.mark.parametrize("private_folder", [".creds", ".no-commit"])
def test_new_asset_cli_sensitive_sources_require_explicit_flag(vault_root: Path, private_folder: str) -> None:
    run_cli(vault_root, "create_area.py", "web-security", "--timestamp", NOTE_TIMESTAMP)
    source = vault_root / private_folder / "private-capture.png"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"secret-content-do-not-print\n")

    result = run_cli(
        vault_root,
        "new_asset.py",
        "image",
        source.as_posix(),
        "--area",
        "web-security",
        "--topic",
        "network-scanning",
        "--title",
        "Private capture",
        "--timestamp",
        NOTE_TIMESTAMP,
    )

    assert result.returncode == 2
    assert f"source under {private_folder}/ requires --sensitive-ok" in result.stderr
    assert "secret-content-do-not-print" not in result.stdout
    assert "secret-content-do-not-print" not in result.stderr
    assert source.is_file()


def test_new_asset_cli_sensitive_source_with_flag_succeeds_without_printing_contents(vault_root: Path) -> None:
    run_cli(vault_root, "create_area.py", "web-security", "--timestamp", NOTE_TIMESTAMP)
    source = vault_root / ".no-commit" / "private-capture.png"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"secret-content-do-not-print\n")

    result = run_cli(
        vault_root,
        "new_asset.py",
        "image",
        source.as_posix(),
        "--area",
        "web-security",
        "--topic",
        "network-scanning",
        "--title",
        "Private capture",
        "--timestamp",
        NOTE_TIMESTAMP,
        "--sensitive-ok",
    )

    target = vault_root / f"04_areas/web-security/assets/images/network-scanning/{NOTE_STEM}_private-capture.png"
    assert result.returncode == 0
    assert target.read_bytes() == b"secret-content-do-not-print\n"
    assert not source.exists()
    assert "secret-content-do-not-print" not in result.stdout
    assert "secret-content-do-not-print" not in result.stderr


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


@pytest.mark.parametrize(
    "relative",
    [
        ".agents/runtime.json",
        ".claude/skills/vault_capture/notes.md",
        ".codex/session.json",
    ],
)
def test_agent_runtime_files_must_be_allowlisted(vault_root: Path, relative: str) -> None:
    path = vault_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}\n", encoding="utf-8")

    assert_has_error(vault_root, "agent file is not in the allowlist")


@pytest.mark.parametrize("private_folder", [".creds", ".no-commit"])
def test_ignored_private_markdown_is_not_read_by_validator(vault_root: Path, private_folder: str) -> None:
    private_file = vault_root / private_folder / "private-note.md"
    private_file.parent.mkdir(parents=True, exist_ok=True)
    private_file.write_text(
        f"{FAKE_OPENAI_KEY}\n[[missing-private-target]]\n",
        encoding="utf-8",
    )

    assert_valid(vault_root)


@pytest.mark.parametrize("tracked", [False, True])
def test_symlink_markdown_fails_validation_without_opening_target(vault_root: Path, tracked: bool) -> None:
    target = vault_root / ".no-commit" / "secret-target.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"{FAKE_OPENAI_KEY}\n", encoding="utf-8")
    link = vault_root / "01_inbox/quick_notes" / f"{NOTE_STEM}_linked-secret.md"
    try:
        os.symlink(target, link)
    except OSError as exc:  # pragma: no cover - platform guard.
        pytest.skip(f"symlink creation is unavailable: {exc}")
    if tracked:
        run(["git", "add", link.relative_to(vault_root).as_posix()], vault_root)

    result = validate(vault_root)

    assert any("symlinks are not allowed" in error for error in result.errors)
    assert not any("possible secret detected" in error for error in result.errors)


def test_rewrite_wikilinks_skips_ignored_private_markdown(vault_root: Path) -> None:
    public_note = write_note(
        vault_root,
        f"01_inbox/quick_notes/{NOTE_STEM}_public-link.md",
        "inbox",
        title="Public Link",
        body="[[old-note]]",
    )
    private_note = vault_root / ".no-commit" / "private-link.md"
    private_note.parent.mkdir(parents=True, exist_ok=True)
    private_note.write_text("[[old-note]]\nsecret-content-do-not-print\n", encoding="utf-8")

    dry_run = run_cli(vault_root, "rewrite_wikilinks.py", "--root", ".", "--from", "old-note", "--to", "new-note")
    write_run = run_cli(
        vault_root,
        "rewrite_wikilinks.py",
        "--root",
        ".",
        "--from",
        "old-note",
        "--to",
        "new-note",
        "--write",
    )

    assert dry_run.returncode == 0
    assert write_run.returncode == 0
    assert public_note.relative_to(vault_root).as_posix() in dry_run.stdout
    assert ".no-commit" not in dry_run.stdout
    assert "secret-content-do-not-print" not in dry_run.stdout
    assert "[[new-note]]" in public_note.read_text(encoding="utf-8")
    assert "[[old-note]]" in private_note.read_text(encoding="utf-8")


def test_list_due_memory_skips_ignored_private_markdown(vault_root: Path) -> None:
    write_note(
        vault_root,
        f"01_inbox/quick_notes/{NOTE_STEM}_public-review.md",
        "inbox",
        title="Public Review",
        extra_frontmatter="review_after: 2026-06-01",
    )
    private_note = vault_root / ".creds" / "private-review.md"
    private_note.parent.mkdir(parents=True, exist_ok=True)
    private_note.write_text(
        note_text("inbox", "Private Review", extra_frontmatter="review_after: 2026-06-01"),
        encoding="utf-8",
    )

    result = run_cli(vault_root, "list_due_memory.py", ".", "--date", "2026-06-09")

    assert result.returncode == 0
    assert "Public Review" in result.stdout
    assert "Private Review" not in result.stdout
    assert ".creds" not in result.stdout
