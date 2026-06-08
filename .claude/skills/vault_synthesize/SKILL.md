---
name: vault_synthesize
description: Create draft synthesis notes without overwriting canonical notes.
---

# Vault Synthesize

## Allowed Reads

- User-selected notes, examples, resources, and templates.

## Allowed Writes

- Draft synthesis notes in `01_inbox/agent_inbox/` or `08_outputs/agent_drafts/`.

## Forbidden Paths

- Existing canonical notes unless explicit approval is given.
- Active runtime config and protected paths listed in `AGENTS.md`.

## Approval Requirements

Ask before promoting a draft into `06_knowledge/synthesis/` or overwriting any note.

## Workflow

Combine selected material into a reviewable draft. Separate evidence, inference, and open questions.
