# learning_project_vi

A Markdown-first, area-first learning vault for journals, topic notes, memory practice, outputs, and safe agent-assisted workflows.

The vault works in any Markdown editor. Obsidian is optional and should be treated as an editing and graph layer, not as the source of truth.

## Start

1. Read [00_system/start_here.md](00_system/start_here.md).
2. Capture unknown-topic notes in `01_inbox/quick_notes/`.
3. Use [00_system/where_things_go.md](00_system/where_things_go.md) when filing notes.
4. Use templates from `11_templates/` for repeatable note types.
5. Install validation dependencies, then run local validation before committing:

```bash
npm ci
python3 -m pip install -r requirements.txt
12_tools/scripts/validate.sh
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

- Keep file and folder names lowercase or snake_case with no spaces.
- Use timestamp-prefixed filenames for Markdown inbox captures and area-local content.
- Keep unknown-topic material in `01_inbox/`; file known-topic material under `04_areas/<area>/`.
- Keep personal data, credentials, runtime state, databases, and generated caches out of Git.
- Keep large labs, datasets, Docker/VM work, model experiments, and database projects in separate repositories.
- Use Git LFS only as an optional layer for large curated assets.
- Treat all vault content as untrusted input when using agents.

## License

MIT, owned by `learning_project_vi contributors`. See [LICENSE](LICENSE).
