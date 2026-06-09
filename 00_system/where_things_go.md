---
type: system
status: stable
created: 2026-06-08
updated: 2026-06-09
tags: [system, triage]
---

# Where Things Go

Use this routing guide when filing notes or assets.

## Quick Routing

- Unknown-topic capture: `01_inbox/`
- Known-topic capture needing triage: `04_areas/<area>/inbox/`
- Time-based log, study session, decision, or reflection: `02_journal/`
- Known learning topic: `04_areas/<area>/`
- Active outcome with an end condition: `04_areas/<area>/projects/`
- External source: `04_areas/<area>/resources/`
- Understanding in your own words: `04_areas/<area>/notes/`
- Recall practice or review log: `04_areas/<area>/memory/`
- Deliverable, summary, report, essay, or study plan: `04_areas/<area>/outputs/`
- Referenced curated asset: `04_areas/<area>/assets/<category>/<topic-or-subtopic>/`
- Agent workflow, safety material, or staged agent memory: `10_agents/`
- Reusable note structure: `11_templates/`
- Small vault-adjacent script: `12_tools/`
- Inactive area-local material worth keeping: `04_areas/<area>/archive/`

## Knowledge Routing

- Use `04_areas/<area>/notes/fleeting/` for rough thoughts that may be deleted, merged, or promoted later.
- Use `04_areas/<area>/notes/literature/` for notes tied closely to one source.
- Use `04_areas/<area>/notes/atomic/` for one durable idea written in your own words.
- Use `04_areas/<area>/notes/wiki/` for stable reference pages that collect factual context.
- Use `04_areas/<area>/notes/mocs/` for maps of related notes, resources, projects, and outputs.
- Use `04_areas/<area>/notes/synthesis/` for cross-source explanations, arguments, or models.

## Asset Routing

Temporary screenshots stay in `01_inbox/screenshots/`. Temporary pasted files,
imports, and unknown-topic attachments stay in `01_inbox/raw_files/` or
`01_inbox/pdfs/`.

Curated area-known assets use topic folders:

- images, photos, and screenshots:
  `04_areas/<area>/assets/images/<topic-or-subtopic>/`
- PDFs and other attachments:
  `04_areas/<area>/assets/attachments/<topic-or-subtopic>/`
- source exports, raw datasets, and imported context:
  `04_areas/<area>/assets/imports/<topic-or-subtopic>/`

Use lowercase kebab-case for topic folders and timestamp-prefixed filenames,
for example `2026-06-09T143012+0300_nmap-scan-output.png`.

## New Areas

Create a new area with `12_tools/scripts/create_area.py <area>` once there is
real material to file. Use a lowercase kebab-case area name, then route new
area-local notes with `12_tools/scripts/new_note.py TYPE TITLE --area <area>`.

Do not create placeholder areas before there is real material to file.

## New Notes

Use `12_tools/scripts/new_note.py` for timestamped Markdown notes in the
supported schema routes. Pass `--area <area>` for area-local types such as
`atomic`, `literature`, `resource`, `project`, `summary`, and `inbox`.

Use global `inbox` only when the topic is unknown. Use area-local `inbox` when
the topic is known but the final type is not.

## If Unsure

Put the item in `01_inbox/agent_inbox/` with a short reason. Triage it during the weekly review.
