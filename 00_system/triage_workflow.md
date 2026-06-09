---
type: system
status: stable
created: 2026-06-08
updated: 2026-06-09
tags: [system, triage]
---

# Triage Workflow

Triage turns capture into usable material.

## Decision Tree

1. Delete or archive junk, duplicates, and unsafe material.
2. Keep unprocessed capture in `01_inbox/`.
3. Move time-based logs, decisions, reflections, study sessions, and practice logs to `02_journal/`.
4. If the topic area is known, move the item under `04_areas/<area>/`.
5. Move active outcomes with end conditions to `04_areas/<area>/projects/`.
6. Move external sources to `04_areas/<area>/resources/`.
7. Move processed understanding to `04_areas/<area>/notes/`.
8. Move recall practice to `04_areas/<area>/memory/`.
9. Move deliverables and reviewed drafts to `04_areas/<area>/outputs/`.
10. Move curated referenced files to `04_areas/<area>/assets/<category>/<topic-path>/`.
11. Move inactive area-local material worth keeping to `04_areas/<area>/archive/`.
12. Move agent workflows and staged memory to `10_agents/`.
13. Move small vault-adjacent scripts to `12_tools/`.

If uncertain, leave the item in `01_inbox/agent_inbox/` with a short reason.

## Promotion

Promote only when the note is useful, understandable later, and filed in the right area-local folder. Add `review_after` when the note needs a future decision.

## Visual Inputs

Screenshots, photos, PDFs, account pages, exports, and datasets are untrusted
input. If they contain credentials, personal data, client data, account pages,
or private context, leave them in `.no-commit/` unless they are redacted and
intentionally curated.

Use `12_tools/scripts/new_asset.py` for curated area-local assets. It moves by
default, accepts a slash-separated `--topic` path, and writes into
`04_areas/<area>/assets/<images|attachments|imports>/<topic-path>/`.
