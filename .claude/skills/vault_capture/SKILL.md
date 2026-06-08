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

## Forbidden Paths

- Any path outside the allowed write scopes.
- Active runtime config and protected paths listed in `AGENTS.md`.

## Approval Requirements

Ask before creating more than 10 files or writing more than 1 MB of Markdown.

## Workflow

Create capture notes with valid frontmatter. Preserve uncertainty instead of filing aggressively.
