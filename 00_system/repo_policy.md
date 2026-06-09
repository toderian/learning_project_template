---
type: system
status: stable
created: 2026-06-08
updated: 2026-06-08
tags: [system, git]
---

# Repo Policy

Keep the template lightweight, portable, and safe to clone.

## Commit

- Markdown notes, templates, and area-local content.
- Small vault-adjacent scripts in `12_tools/scripts/`.
- Light Obsidian config from the allowlist.
- Agent skill files in `.agents/skills/` and `.claude/skills/`.
- Curated small assets referenced by notes.

## Ignore

- secrets and `.env` files;
- logs, caches, generated outputs, and runtime state;
- vector databases, transcript databases, local sidecar state, and Chroma stores;
- active MCP, hook, or auto-run agent config;
- large generated binaries.

## Do Not Broadly Ignore Agent Directories

Do not use broad ignore patterns such as `.agents/`, `.claude/`, or `.codex/`. The public template commits skills and documentation while ignoring only active runtime config files:

- `.mcp.json`
- `.codex/config.toml`
- `.codex/hooks.json`
- `.claude/settings.json`
- `.claude/settings.local.json`

## External Labs

Use separate repositories for Docker or VM labs, database projects, cyber ranges, fine-tuning experiments, GPU work, model-heavy work, large datasets, and standalone software projects.

Record project-specific external repo notes under the relevant `04_areas/<area>/resources/` folder with `11_templates/external_repo.md`.
