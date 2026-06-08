---
type: system
status: stable
created: 2026-06-08
updated: 2026-06-08
tags: [system, schema]
---

# Schema

This file is the source of truth for note types, default folders, default templates, and required example coverage. Validation derives allowed `type` values and expected templates from the table below.

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

| Type | Tier | Default Folder | Default Template | Example Required |
| --- | --- | --- | --- | --- |
| `system` | extended | `00_system/` | none | no |
| `inbox` | core | `01_inbox/quick_notes/` | `inbox_note.md` | no |
| `journal` | core | `02_journal/daily/` | `daily_note.md` | no |
| `weekly_review` | extended | `02_journal/weekly/` | `weekly_review.md` | no |
| `monthly_review` | extended | `02_journal/monthly/` | `monthly_review.md` | no |
| `quarterly_review` | extended | `02_journal/quarterly/` | `quarterly_review.md` | no |
| `yearly_review` | extended | `02_journal/yearly/` | `yearly_review.md` | no |
| `decision` | extended | `02_journal/decisions/` | `decision.md` | no |
| `reflection` | extended | `02_journal/reflections/` | `reflection.md` | no |
| `project` | core | `03_projects/` | `project.md` | yes |
| `area` | core | `04_areas/` | `area.md` | yes |
| `resource` | core | `05_resources/` | `resource.md` | no |
| `course` | extended | `05_resources/courses/` | `course.md` | yes |
| `book` | extended | `05_resources/books/` | `book.md` | no |
| `paper` | extended | `05_resources/papers/` | `paper.md` | yes |
| `documentation` | extended | `05_resources/documentation/` | `documentation.md` | no |
| `video` | extended | `05_resources/videos/` | `video.md` | no |
| `fleeting` | extended | `06_knowledge/fleeting/` | `fleeting_note.md` | no |
| `literature` | extended | `06_knowledge/literature/` | `literature_note.md` | no |
| `atomic` | core | `06_knowledge/atomic/` | `atomic_note.md` | yes |
| `wiki` | extended | `06_knowledge/wiki/` | `wiki_page.md` | no |
| `moc` | core | `06_knowledge/mocs/` | `moc.md` | yes |
| `synthesis` | extended | `06_knowledge/synthesis/` | `synthesis.md` | no |
| `flashcard` | core | `07_memory/spaced_repetition/` | `flashcard_deck.md` | yes |
| `retrieval_practice` | core | `07_memory/retrieval_practice/` | `retrieval_practice.md` | no |
| `review_log` | extended | `07_memory/review_logs/` | `review_log.md` | no |
| `output` | core | `08_outputs/` | `output.md` | no |
| `summary` | extended | `08_outputs/summaries/` | `summary.md` | yes |
| `report` | extended | `08_outputs/reports/` | `report.md` | no |
| `essay` | extended | `08_outputs/essays/` | `essay.md` | no |
| `study_plan` | extended | `08_outputs/study_plans/` | `study_plan.md` | no |
| `agent_draft` | extended | `08_outputs/agent_drafts/` | `agent_draft.md` | no |
| `agent_memory` | extended | `10_agents/memory/candidates/` | none | no |
| `external_repo` | extended | `05_resources/external_repos.md` | `external_repo.md` | no |
| `tool` | extended | `12_tools/` | `tool.md` | no |
| `asset` | extended | `09_assets/` | none | no |
| `study_session` | extended | `02_journal/daily/` | `study_session.md` | no |
| `practice_log` | extended | `02_journal/daily/` | `practice_log.md` | no |
| `error_log` | extended | `02_journal/reflections/` | `error_log.md` | no |
| `exam_prep_project` | extended | `03_projects/` | `exam_prep_project.md` | no |
| `archive` | extended | `99_archive/` | none | no |

## Date Rules

- `created`, `updated`, and `review_after` use `YYYY-MM-DD` when populated.
- Card-level `due::` also uses `YYYY-MM-DD`.
- Empty date fields are allowed in reusable templates.

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
