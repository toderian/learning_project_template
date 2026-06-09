---
type: system
status: stable
created: 2026-06-08
updated: 2026-06-09
tags: [system, lfs]
---

# Git LFS Policy

Git LFS is optional. The public template works without it.

Curated assets under `04_areas/<area>/assets/` must use Git LFS when they are
larger than 5 MB. Non-asset files above 5 MB produce a warning, and non-asset
files above 25 MB must use Git LFS.

## Use LFS For

- large curated PDFs;
- large image assets;
- audio or video source files;
- large diagrams;
- small-to-medium reusable datasets worth versioning.

## Do Not Use LFS For

- generated outputs;
- caches;
- logs;
- vector databases;
- transcript databases;
- VM images;
- model checkpoints;
- database dumps;
- heavy lab datasets.

Those belong in external storage or separate lab repositories.

## Opt In

To use the example LFS rules:

```bash
git lfs install
cp .gitattributes.example .gitattributes
git lfs track "04_areas/**/assets/attachments/**/*.pdf"
git add .gitattributes
git add "04_areas/<area>/assets/attachments/large-file.pdf"
git commit -m "track large asset with git lfs"
```

After cloning a repo that uses LFS:

```bash
git lfs pull
```

Use "fetch/materialize LFS files locally" in docs unless a future version adds true external mount workflows.
