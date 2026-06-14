# ACCEPTED — A1/A2 live maintenance and workbook enrichment

**Status:** ACCEPTED
**Decided on:** 2026-06-14
**Scope:** A1/A2 live-course maintenance, activity/workbook enrichment, and future bug-fix PRs.

## Decision

A1 and A2 initial builds are shipped and live. Future A1/A2 work is **live maintenance**, not a continuation of the initial-build pipeline debate.

For future A1/A2 changes:

- Prefer workbook-tab/activity enrichment over rewriting shipped lesson prose.
- Fix real user-facing bugs with small, module-scoped PRs.
- Do not run whole-level rebuilds unless the user explicitly requests one.
- Preserve existing activity IDs when practical. If a module already uses `wb-1` through `wb-11`, append new workbook activities with a clear extension pattern rather than renumbering existing live exercises.
- Validate activity schema, MDX rendering, and affected site output before shipping.
- Keep generated `status/*.json`, `audit/*-review.md`, `review/*-review.md`, and session-state files out of PRs.

## Rationale

Learners are already using A1/A2. Stability matters more than re-litigating the writer pipeline that produced the first live version. The expected future improvement path is richer practice in Workbook tabs, plus targeted corrections where live behavior or language quality requires it.

## Supersedes

- `dec-002` for A1/A2 initial-build writer assignment.
- Pending A1/A2 build-blocker cards retired on 2026-06-14, including the V7.1 wiki-driven writer and prompt-generator cards.
