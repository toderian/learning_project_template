# 04_areas

Area-first learning domains live here. Create an area only when you have a real
topic to file.

Use lowercase kebab-case area names, for example `04_areas/web-security/`.

Create the skeleton with:

```bash
12_tools/scripts/create_area.py web-security
```

The helper creates `README.md` from `11_templates/area.md`, creates the
standard subdirectories, and refuses to overwrite an existing area. Use
`--title "Web Security"` when the display title should differ from the folder
name.

```text
04_areas/<area>/
  README.md
  inbox/
  resources/
    books/
    courses/
    documentation/
    papers/
    videos/
  notes/
    fleeting/
    literature/
    atomic/
    wiki/
    mocs/
    synthesis/
  memory/
    spaced_repetition/
    retrieval_practice/
    review_logs/
  projects/
  outputs/
    summaries/
    reports/
    essays/
    study_plans/
  assets/
    attachments/
      <topic-path>/
    images/
      <topic-path>/
    imports/
      <topic-path>/
  archive/
```

Unknown-topic capture stays in `01_inbox/`. Once the area is known, file new
material under the matching area folder.

Use `12_tools/scripts/new_note.py TYPE TITLE --area <area>` for timestamped
area-local Markdown notes. Use `new_note.py inbox TITLE --area <area>` for
known-topic captures that still need triage.

Curated images, photos, screenshots, PDFs, and other attachments should be
filed with `12_tools/scripts/new_asset.py` under
`assets/<category>/<topic-path>/` with timestamp-prefixed filenames. Use
slash-separated lowercase kebab-case topic paths, for example
`sql-injection/login-forms`.
