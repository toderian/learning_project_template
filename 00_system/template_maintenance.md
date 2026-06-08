---
type: system
status: stable
created: 2026-06-08
updated: 2026-06-08
tags: [system, maintenance]
---

# Vault Maintenance

Treat the numbered top-level folders as stable structure. Renumber only when the benefit is worth updating links, docs, and habits.

## Change Rules

- Update `00_system/schema.md` before adding or removing note types.
- Add every non-`none` template listed in the schema table.
- Keep examples generic, safe to publish, and link-complete.
- Keep `_prompts/plans/` as historical planning/reference material.
- Keep root docs, CI, scripts, policy files, templates, and Obsidian defaults aligned with how this vault is actually used.
- Run `12_tools/scripts/validate.sh` before committing.
- Keep validation logic in dedicated files under `12_tools/scripts/`; do not embed large inline validators in shell wrappers or CI workflow YAML.

## Versioning

Prefer small, reviewable changes. For multi-device usage, pull before editing daily notes on another device and resolve Markdown conflicts manually.
