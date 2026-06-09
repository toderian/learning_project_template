---
type: system
status: stable
created: 2026-06-08
updated: 2026-06-08
tags: [system, schema]
---

# Schema

This file is the source of truth for note types, default routes, and default templates. Validation derives allowed `type` values, route patterns, and expected templates from the table below.

## Default Frontmatter

```yaml
---
type:
status:
created:
updated:
tags: []
---
```

Allowed `status` values:

```text
inbox
draft
active
review
stable
done
archived
```

Optional fields:

```yaml
source:
url:
author:
aliases: []
review_after:
confidence:
```

Allowed `confidence` values are `low`, `medium`, and `high`. Confidence means reliability as reusable knowledge, not memory strength.

## Type Table

Route patterns use `*` for one area folder name.

| Type | Tier | Default Folder | Default Template |
| --- | --- | --- | --- |
| `system` | extended | `00_system/` | none |
| `inbox` | core | `01_inbox/quick_notes/` | `inbox_note.md` |
| `journal` | core | `02_journal/daily/` | `daily_note.md` |
| `weekly_review` | extended | `02_journal/weekly/` | `weekly_review.md` |
| `monthly_review` | extended | `02_journal/monthly/` | `monthly_review.md` |
| `quarterly_review` | extended | `02_journal/quarterly/` | `quarterly_review.md` |
| `yearly_review` | extended | `02_journal/yearly/` | `yearly_review.md` |
| `decision` | extended | `02_journal/decisions/` | `decision.md` |
| `reflection` | extended | `02_journal/reflections/` | `reflection.md` |
| `area` | core | `04_areas/*/README.md` | `area.md` |
| `project` | core | `04_areas/*/projects/` | `project.md` |
| `exam_prep_project` | extended | `04_areas/*/projects/` | `exam_prep_project.md` |
| `resource` | core | `04_areas/*/resources/` | `resource.md` |
| `course` | extended | `04_areas/*/resources/courses/` | `course.md` |
| `book` | extended | `04_areas/*/resources/books/` | `book.md` |
| `paper` | extended | `04_areas/*/resources/papers/` | `paper.md` |
| `documentation` | extended | `04_areas/*/resources/documentation/` | `documentation.md` |
| `video` | extended | `04_areas/*/resources/videos/` | `video.md` |
| `external_repo` | extended | `04_areas/*/resources/` | `external_repo.md` |
| `fleeting` | extended | `04_areas/*/notes/fleeting/` | `fleeting_note.md` |
| `literature` | extended | `04_areas/*/notes/literature/` | `literature_note.md` |
| `atomic` | core | `04_areas/*/notes/atomic/` | `atomic_note.md` |
| `wiki` | extended | `04_areas/*/notes/wiki/` | `wiki_page.md` |
| `moc` | core | `04_areas/*/notes/mocs/` | `moc.md` |
| `synthesis` | extended | `04_areas/*/notes/synthesis/` | `synthesis.md` |
| `flashcard` | core | `04_areas/*/memory/spaced_repetition/` | `flashcard_deck.md` |
| `retrieval_practice` | core | `04_areas/*/memory/retrieval_practice/` | `retrieval_practice.md` |
| `review_log` | extended | `04_areas/*/memory/review_logs/` | `review_log.md` |
| `output` | core | `04_areas/*/outputs/` | `output.md` |
| `summary` | extended | `04_areas/*/outputs/summaries/` | `summary.md` |
| `report` | extended | `04_areas/*/outputs/reports/` | `report.md` |
| `essay` | extended | `04_areas/*/outputs/essays/` | `essay.md` |
| `study_plan` | extended | `04_areas/*/outputs/study_plans/` | `study_plan.md` |
| `agent_draft` | extended | `01_inbox/agent_inbox/` | `agent_draft.md` |
| `agent_memory` | extended | `10_agents/memory/candidates/` | none |
| `tool` | extended | `12_tools/` | `tool.md` |
| `asset` | extended | `04_areas/*/assets/` | none |
| `study_session` | extended | `02_journal/daily/` | `study_session.md` |
| `practice_log` | extended | `02_journal/daily/` | `practice_log.md` |
| `error_log` | extended | `02_journal/reflections/` | `error_log.md` |
| `archive` | extended | `04_areas/*/archive/` | none |

## Date Rules

- `created` and `updated` should use full ISO 8601 timestamps with timezone for new area and inbox notes, for example `2026-06-09T14:30:12+03:00`.
- Existing system docs and reusable templates may use empty values or date-only `YYYY-MM-DD` values.
- `review_after` stays date-only `YYYY-MM-DD`.
- Card-level `due::` also uses `YYYY-MM-DD`.
- Empty date fields are allowed in reusable templates.

## Filename Rules

Area-local content and Markdown inbox captures use filesystem-safe local Europe/Bucharest datetime prefixes:

```text
YYYY-MM-DDTHHMMSS+HHMM_2-to-4-word-slug.md
```

Curated area-local assets use the same stem convention, for example:

```text
2026-06-09T143012+0300_nmap-scan-output.png
```

`README.md`, system docs, templates, journal notes, and agent/tool docs are exempt.

## Memory Card Convention

```text
### card_id

due:: YYYY-MM-DD
interval_days:: 1
ease:: 2.50
state:: new | learning | review | suspended

q:: Question text
a:: Answer text
```
