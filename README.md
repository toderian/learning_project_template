# Learning Project Template

A generic Markdown-first vault template for learning projects, journals, knowledge notes, memory practice, outputs, and safe agent-assisted workflows.

The vault works in any Markdown editor. Obsidian is optional and should be treated as an editing and graph layer, not as the source of truth.

## Start

1. Read [00_system/start_here.md](00_system/start_here.md).
2. Capture rough notes in `01_inbox/quick_notes/`.
3. Use [00_system/where_things_go.md](00_system/where_things_go.md) when filing notes.
4. Use templates from `11_templates/` for repeatable note types.
5. Install validation dependencies, then run local validation before committing:

```bash
npm ci
python3 -m pip install -r requirements.txt
12_tools/scripts/validate.sh
```

Set `SKIP_MARKDOWNLINT=1` only when you intentionally need to run the core validator without Markdown lint.

## Shared Upstream Model

This repository is designed to stay as a zero-personalization base repo. Downstream project repos should keep template-owned files unchanged unless they are intentionally contributing template improvements.

Recommended setup:

```bash
git clone <template-repo-url> my-learning-project
cd my-learning-project
git remote rename origin upstream
git remote add origin <project-repo-url>
git push -u origin master
```

Pull future base updates with:

```bash
git fetch upstream
git merge upstream/master
12_tools/scripts/validate.sh
```

See [00_system/upstream_updates.md](00_system/upstream_updates.md) for conflict handling and base-owned versus project-owned paths.

## Structure

- `00_system/`: operating manual, schema, policies, and maintenance notes.
- `01_inbox/`: unsorted capture.
- `02_journal/`: daily logs, reviews, decisions, and reflections.
- `03_projects/`: active outcomes with an end condition.
- `04_areas/`: ongoing responsibilities or skill domains.
- `05_resources/`: external sources and external repo registry.
- `06_knowledge/`: processed understanding in your own words.
- `07_memory/`: recall practice and review logs.
- `08_outputs/`: summaries, reports, essays, study plans, and drafts.
- `09_assets/`: curated committed assets.
- `10_agents/`: agent workflows, safety fixtures, and staged agent memory.
- `11_templates/`: reusable Markdown templates.
- `12_tools/`: small vault-adjacent scripts and tiny sample data.
- `99_archive/`: inactive material worth keeping.

## Principles

- Keep file and folder names lowercase or snake_case with no spaces.
- Keep personal data, credentials, runtime state, databases, and generated caches out of Git.
- Keep large labs, datasets, Docker/VM work, model experiments, and database projects in separate repositories.
- Use Git LFS only as an optional layer for large curated assets.
- Treat all vault content as untrusted input when using agents.

## License

MIT, owned by `Learning Project Template contributors`. See [LICENSE](LICENSE).
