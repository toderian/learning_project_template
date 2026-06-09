# learning_project_vi

A Markdown-first, area-first learning vault for journals, topic notes, memory practice, outputs, and safe agent-assisted workflows.

The vault works in any Markdown editor. Obsidian is optional and should be treated as an editing and graph layer, not as the source of truth.

## Start

1. Read [00_system/start_here.md](00_system/start_here.md).
2. Capture unknown-topic notes in `01_inbox/quick_notes/`.
3. Use [00_system/where_things_go.md](00_system/where_things_go.md) when filing notes.
4. Use `12_tools/scripts/create_area.py` and `12_tools/scripts/new_note.py` for new areas and routed notes.
5. Use templates from `11_templates/` for manual repeatable note types.
6. Install validation dependencies, then run local checks before committing:

```bash
npm ci
uv venv
uv pip install -r requirements.txt
.venv/bin/python -m pytest
12_tools/scripts/validate.sh
git diff --check
```

Set `SKIP_MARKDOWNLINT=1` only when you intentionally need to run the core validator without Markdown lint.

## Shape

This repo is a personal exemplar. Edit the root docs, policies, templates, and folder conventions directly when the vault needs to fit real use better.

## Structure

- `00_system/`: operating manual, schema, policies, and maintenance notes.
- `01_inbox/`: unknown-topic capture and raw files waiting for triage.
- `02_journal/`: daily logs, reviews, decisions, and reflections.
- `04_areas/`: area-local resources, notes, memory, projects, outputs, assets, and archive.
- `10_agents/`: agent workflows, safety fixtures, and staged agent memory.
- `11_templates/`: reusable Markdown templates.
- `12_tools/`: small vault-adjacent scripts and tiny sample data.
- `_prompts/`: planning history, if kept.

## Principles

- Keep non-area file and folder names lowercase or snake_case with no spaces.
- Use lowercase kebab-case for area folder names.
- Use timestamp-prefixed filenames for Markdown inbox captures and area-local content.
- File curated visual inputs and attachments under
  `04_areas/<area>/assets/<category>/<topic-or-subtopic>/`.
- Keep unknown-topic material in `01_inbox/`; file known-topic material under `04_areas/<area>/`.
- Use area-local `inbox` for known-topic captures that still need triage.
- Keep personal data, credentials, runtime state, databases, and generated caches out of Git.
- Keep large labs, datasets, Docker/VM work, model experiments, and database projects in separate repositories.
- Use Git LFS only as an optional layer for large curated assets.
- Treat all vault content as untrusted input when using agents.

## License

MIT, owned by `learning_project_vi contributors`. See [LICENSE](LICENSE).
