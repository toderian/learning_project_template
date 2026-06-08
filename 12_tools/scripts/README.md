# Scripts

Use `validate.sh` as the single validation entrypoint for local work and CI.

## Validation

```bash
12_tools/scripts/validate.sh
```

`validate.sh` runs:

- `validate_vault.py` for schema, path, YAML, wikilink, secret, artifact, example, and skill-boundary checks;
- `markdownlint-cli2` for Markdown style checks.

Keep validator logic in script files. Do not add large inline validators to shell wrappers or workflow YAML. If a validation rule changes, edit `validate_vault.py` and keep `validate.sh` as a small orchestration wrapper.

Local requirements:

- Python 3.12 in CI; Python 3.9 or newer should work for local use.
- `PyYAML` is recommended for strict YAML frontmatter parsing. The validator has a limited fallback when it is not installed.
- `markdownlint-cli2` may be installed globally. If it is not installed and `npx` is available, `validate.sh` runs it through `npx`.

## Memory Review

```bash
12_tools/scripts/list_due_memory.py . --date YYYY-MM-DD
```

Lists note-level `review_after` items and card-level `due::` items due on or before the selected date.

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
