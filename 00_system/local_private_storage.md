---
type: system
status: stable
created: 2026-06-09
updated: 2026-06-09
tags: [system, git, agents, secrets]
---

# Local Private Storage

Use these folders for local material that must not be committed.

## `.creds/`

Store credentials, keys, tokens, and private service config here when an agent or local tool needs access.

Agent rules:

- Use `.creds/` only for explicit user-requested tasks.
- Read the minimum needed file.
- Do not print, summarize, copy, or transform secret values.
- Prefer passing secrets through environment variables or standard CLI config.
- Do not write secrets into notes, logs, prompts, generated outputs, or commits.
- Do not force-add `.creds/` to Git.

## `.no-commit/`

Store local scratch files, private imports, experiments, and other material that should remain outside Git.

Agent rules:

- Read or write `.no-commit/` only when the user asks for private local files or scratch work.
- Do not use it as a hidden source of vault truth.
- Do not force-add `.no-commit/` to Git.

Both folders are intentionally ignored by `.gitignore`.

Validation expects `.gitignore` to ignore:

- `.creds/`
- `.no-commit/`
- `.env`
- `.env.*`

Do not add unignore rules for these private paths. Validation should fail if
content under `.creds/` or `.no-commit/` is tracked, even by force-add.
