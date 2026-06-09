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

## Local Checks

Run the same checks before committing:

```bash
uv venv
uv pip install -r requirements.txt
.venv/bin/python -m pytest
12_tools/scripts/validate.sh
git diff --check
```

`git diff --check` catches whitespace errors that the validator may not report.

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
