---
name: vault_capture
description: Capture new raw notes into the inbox with safe frontmatter.
---

# Vault Capture

## Allowed Reads

- `00_system/schema.md`
- `00_system/where_things_go.md`
- Existing inbox notes for naming context.

## Allowed Writes

- `01_inbox/quick_notes/`
- `01_inbox/agent_inbox/`
- `04_areas/*/inbox/`

## Forbidden Paths

- Any path outside the allowed write scopes.
- Active runtime config and protected paths listed in `AGENTS.md`.

## Approval Requirements

Ask before creating more than 10 files or writing more than 1 MB of Markdown.

## Workflow

Create capture notes with valid frontmatter and timestamp-prefixed filenames. Use the global inbox when the area is unknown; use `04_areas/*/inbox/` when the area is already clear. Preserve uncertainty instead of filing aggressively.
