---
type: system
status: stable
created: 2026-06-08
updated: 2026-06-08
tags: [system, git, upstream]
---

# Upstream Updates

This template is meant to stay connected as a shared upstream. A downstream learning project should not need to personalize root docs, license text, CI, scripts, Obsidian config, templates, or policy files just to start using the vault.

## Initial Setup

After cloning the base repository, keep it as `upstream` and add the project repository as `origin`:

```bash
git remote rename origin upstream
git remote add origin <project-repo-url>
git push -u origin master
```

## Normal Update Flow

```bash
git fetch upstream
git merge upstream/master
12_tools/scripts/validate.sh
```

Resolve conflicts in normal Git flow, then rerun validation before pushing to the project remote.

## Conflict Handling

Prefer upstream changes for base-owned files unless the downstream repo is intentionally carrying a local template fork. Prefer project changes for project-owned notes and assets.

Base-owned paths:

- root policy and setup files such as `README.md`, `AGENTS.md`, `CLAUDE.md`, `LICENSE`, `.github/`, `.gitignore`, and `.markdownlint-cli2.yaml`
- `00_system/`, `11_templates/`, and `12_tools/scripts/`
- committed agent skills under `.agents/skills/` and `.claude/skills/`
- light committed Obsidian config under `.obsidian/`

Project-owned paths:

- captured notes in `01_inbox/`
- journals, projects, areas, resources, knowledge notes, memory decks, outputs, assets, and archive folders
- appended entries in `05_resources/external_repos.md`
- staged memory candidates in `10_agents/memory/candidates/`

When a conflict crosses those boundaries, preserve the downstream content and copy any useful new template guidance into the appropriate project note rather than editing base-owned policy casually.

## Validation

Use `12_tools/scripts/validate.sh` after every upstream merge. It runs core vault validation plus markdownlint. Use `SKIP_MARKDOWNLINT=1` only for a deliberate core-only check.
