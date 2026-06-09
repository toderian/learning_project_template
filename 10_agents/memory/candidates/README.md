# Candidates

Candidate agent memory notes waiting for human review.

Agents may stage bounded candidate notes here when memory-update work is requested. Human review is required before promotion into any active memory system.

## Candidate Structure

Use `type: agent_memory` for candidate notes. Include these sections:

- Proposed memory: the concise memory text being suggested.
- Evidence/source: the user request, file path, or other source that supports it.
- Scope: where the memory should apply and any limits.
- Confidence: `low`, `medium`, or `high`.
- Review/expiry: when to revisit, expire, or delete the candidate.
- Human decision: pending, approved, rejected, or revised.
