---
name: vault_memory_update
description: Stage candidate agent memory updates for human approval.
---

# Vault Memory Update

## Allowed Reads

- User-approved notes and existing memory candidates.

## Allowed Writes

- `10_agents/memory/candidates/`

## Forbidden Paths

- Active memory outside the candidate area.
- Active runtime config and protected paths listed in `AGENTS.md`.

## Approval Requirements

Promotion to active memory requires explicit approval.

## Workflow

Write concise candidate memory notes with source references and uncertainty. Do not self-promote candidates.
