---
type: system
status: stable
created: 2026-06-08
updated: 2026-06-08
tags: [system, obsidian]
---

# Obsidian Policy

The vault must work as plain Markdown and open usefully in Obsidian with restricted mode on.

## Allowed Committed Config

Only these `.obsidian` files are part of the public template:

- `.obsidian/core-plugins.json`
- `.obsidian/templates.json`
- `.obsidian/daily-notes.json`
- `.obsidian/app.json`

`app.json` should contain only portable attachment and default-folder settings.

## Ignored Runtime Config

Do not commit:

- `.obsidian/workspace*.json`
- `.obsidian/plugins/`
- `.obsidian/themes/`
- `.obsidian/hotkeys.json`
- `.obsidian/community-plugins.json`

## Optional Enhancements

Canvas, Mermaid, Dataview, Templater, spaced repetition plugins, FSRS-compatible workflows, and Obsidian MCP connectors may be documented as optional. None are required for base vault behavior.
