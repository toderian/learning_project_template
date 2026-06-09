---
type: system
status: stable
created: 2026-06-08
updated: 2026-06-09
tags: [system]
---

# Start Here

This vault is a Markdown-first, area-first learning project. Use it for capture, journaling, area-local resources, knowledge notes, recall practice, outputs, and safe agent-assisted workflows.

## First Five Minutes

1. Capture unknown-topic notes in `01_inbox/quick_notes/`.
2. File anything obvious using [where_things_go.md](where_things_go.md).
3. Start daily notes from `11_templates/daily_note.md`.
4. Create real topic areas with `12_tools/scripts/create_area.py <area>`.
5. Create routed notes with `12_tools/scripts/new_note.py TYPE TITLE`.
6. Run local checks before committing.

## Daily Use

- Capture first; sort later when the area is unclear.
- Prefer small notes with clear titles.
- Use `review_after` for whole-note review.
- Use `due::` for card-level memory practice.
- Use timestamp-prefixed filenames for Markdown inbox captures and area-local content.
- Keep generated outputs, databases, caches, secrets, and local runtime state out of Git.

## Local Checks

```bash
uv venv
uv pip install -r requirements.txt
.venv/bin/python -m pytest
12_tools/scripts/validate.sh
git diff --check
```

## Knowledge Note Types

- Fleeting notes are short, temporary captures of thoughts that are not ready to become reusable knowledge.
- Literature notes summarize or quote an external source, with enough citation context to return to that source.
- Atomic notes state one reusable idea in your own words.
- Wiki notes collect stable reference material that benefits from a more encyclopedia-like page.
- MOCs map related notes and resources so a topic can be navigated quickly.
- Synthesis notes combine multiple sources or notes into a higher-level argument, model, or explanation.

## Optional Layers

Obsidian, community plugins, MCP tools, sidecar memory systems, and Git LFS are optional. The vault should remain useful with plain Markdown and Git only.
