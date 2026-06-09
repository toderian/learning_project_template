---
name: vault_triage
description: Propose inbox filing and perform approved moves with wikilink updates.
---

# Vault Triage

## Allowed Reads

- `00_system/where_things_go.md`
- `00_system/schema.md`
- Notes relevant to the triage batch.

## Allowed Writes

- Move or rename approved notes only after user approval.
- Move known-topic material into `04_areas/*/` routes.
- Update inbound wikilinks with `12_tools/scripts/rewrite_wikilinks.py` or an equivalent reviewed process.

## Forbidden Paths

- Protected paths listed in `AGENTS.md` without explicit approval.
- Runtime config, databases, caches, and generated state.

## Approval Requirements

Propose moves by default. Ask before moving, renaming, deleting, archiving, or rewriting links.

## Workflow

Classify each item, explain the area-local destination, and identify link updates. Route known-topic material into the relevant `04_areas/*/` folder and leave unknown-topic material in the global inbox. If link rewriting is unsafe, leave files in place and produce a proposal.
