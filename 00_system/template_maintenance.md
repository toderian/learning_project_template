---
type: system
status: stable
created: 2026-06-08
updated: 2026-06-08
tags: [system, maintenance]
---

# Template Maintenance

Treat the numbered top-level folders as public structure. Do not renumber them after publishing a release.

## Change Rules

- Update `00_system/schema.md` before adding or removing note types.
- Add every non-`none` template listed in the schema table.
- Keep examples generic, safe to publish, and link-complete.
- Keep `_prompts/plans/` as reference material in this repo. End-user vaults may delete it after cloning.
- Run `12_tools/scripts/validate.sh` before committing.

## Versioning

Prefer small, reviewable changes. For multi-device usage, pull before editing daily notes on another device and resolve Markdown conflicts manually.
