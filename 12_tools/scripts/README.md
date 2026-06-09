# Scripts

Use `validate.sh` as the single validation entrypoint for local work and CI.

## Creation Helpers

Create a new area:

```bash
12_tools/scripts/create_area.py web-security
12_tools/scripts/create_area.py web-security --title "Web Security" --dry-run
```

`create_area.py` expects a lowercase kebab-case `AREA` name. It creates the
standard `04_areas/<area>/` skeleton, renders `README.md` from
`11_templates/area.md`, and refuses existing areas. There is no force mode.

Create a timestamped note:

```bash
12_tools/scripts/new_note.py atomic "SQL injection basics" --area web-security
12_tools/scripts/new_note.py inbox "Untyped capture"
12_tools/scripts/new_note.py inbox "Known capture" --area web-security
```

`new_note.py` routes notes from `00_system/schema.md`. Area-local note types
require `--area` and an existing `04_areas/<area>/README.md`; the helper does
not create areas automatically. Global routes are `inbox` and `agent_draft`.
Use area-local `inbox` when the topic is known but the final note type is not.

Both helpers accept:

- `--root ROOT` for another vault root.
- `--timestamp ISO_DATETIME` for a timezone-aware creation time.
- `--dry-run` to inspect planned writes.

`new_note.py` also accepts `--slug SLUG`. Use it when a title cannot produce a
safe two- to four-word ASCII slug. Unsupported creation types include `area`,
`asset`, `system`, journal and review types, and `tool`.

File a curated asset:

```bash
12_tools/scripts/new_asset.py image ~/Desktop/nmap.png --area web-security --topic network-scanning --title "Nmap scan output"
12_tools/scripts/new_asset.py pdf ./lab-notes.pdf --area web-security --topic sql-injection/login-forms --title "Login form lab notes" --copy
12_tools/scripts/new_asset.py import ./chat-export.json --area web-security --topic ai-assisted-review --slug exported-chat
```

`new_asset.py` moves the source file by default into
`04_areas/<area>/assets/<images|attachments|imports>/<topic-path>/` with a
timestamp-prefixed filename. Use `--copy` when the source should remain in
place. Use `--dry-run` to print the source, action, and target before changing
files.

Asset categories route as follows:

- `image`, `images`, `photo`, and `screenshot` route to `assets/images/`.
- `attachment`, `attachments`, and `pdf` route to `assets/attachments/`.
- `import`, `imports`, `dataset`, and `export` route to `assets/imports/`.

Pass a single `--topic` path such as `network-scanning` or
`sql-injection/login-forms`. Each segment must be lowercase kebab-case. The
target slug comes from `--slug`, then `--title`, then the source filename stem;
it must be two to four lowercase ASCII words. Source extensions must already be
lowercase and compatible with the selected category. Curated assets over 5 MB
must be tracked by Git LFS. Sources under `.creds/` or `.no-commit/` require
`--sensitive-ok` after manual review. Do not curate sensitive screenshots,
photos, PDFs, or account pages unless they have been redacted and are
intentionally safe to keep in Git.

## Local Checks

Run the same checks before committing:

```bash
uv venv
uv pip install -r requirements.txt
.venv/bin/python -m pytest
12_tools/scripts/validate.sh
docker run --rm -v "$PWD:/repo" -w /repo ghcr.io/gitleaks/gitleaks:v8.30.1 git --redact --no-banner .
git diff --check
```

`git diff --check` catches whitespace errors that the validator may not report.
The Gitleaks command scans git history and redacts detected secret values.

## Validation

```bash
12_tools/scripts/validate.sh
```

`validate.sh` runs:

- `validate_vault.py` for schema, route, filename, YAML, wikilink, secret, artifact, and skill-boundary checks;
- `markdownlint-cli2` for Markdown style checks.

Keep validator logic in script files. Do not add large inline validators to shell wrappers or workflow YAML. If a validation rule changes, edit `validate_vault.py` and keep `validate.sh` as a small orchestration wrapper.

Local requirements:

- Python 3.12 in CI; Python 3.9 or newer should work for local use.
- Use `uv venv` and `uv pip install -r requirements.txt` when local Python dependencies are needed.
- Install Node dependencies with `npm ci`.
- `markdownlint-cli2` is required by default. Set `SKIP_MARKDOWNLINT=1` only for an intentional core-only validation run.

## Memory Review

```bash
12_tools/scripts/list_due_memory.py . --date YYYY-MM-DD
```

Lists note-level `review_after` items and card-level `due::` items due on or before the selected date.

Notes tagged `example`, if any exist, are skipped by default. Add `--include-examples` to include them.

## Wikilink Rewrites

Dry-run an approved move or rename:

```bash
12_tools/scripts/rewrite_wikilinks.py --root . --from old_note --to new_note
```

Write changes only after approval:

```bash
12_tools/scripts/rewrite_wikilinks.py --root . --from old_note --to new_note --write
```

The rewrite helper ignores fenced code blocks and refuses ambiguous bare note names.
