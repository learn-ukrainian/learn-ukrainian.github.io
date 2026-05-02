# Pending Decisions

> **Convention introduced:** 2026-05-02
> **Reference:** [`docs/best-practices/agent-cooperation.md`](../../best-practices/agent-cooperation.md) — "Multi-Agent Deliberation" section, "Decision Card pattern"

## What lives here

Decision Cards emitted by the orchestrator (Claude) **when the user is AFK** and a decision needs the user's input before work can proceed. Each file is a single Decision Card surfaced from a multi-agent `ab discuss` deliberation OR from any other point where the orchestrator has hit a real choice that's not its to make.

This directory is **the canonical AFK queue.** Cold-start protocol scans it. Anything in here is BLOCKING for its declared scope — orchestrator must NOT start new work that could invalidate a pending decision.

## File naming

```
{YYYY-MM-DD}-{kebab-case-slug}.md
```

Examples:
- `2026-05-02-poc-checkpoint-a-failure-handling.md`
- `2026-05-08-module-type-categories.md`

Date = when the decision was surfaced, not when it'll be resolved.

## File structure

Each file contains exactly one Decision Card per the template in `agent-cooperation.md` ("Decision Card pattern" section). Don't bundle multiple decisions in one file — one card per file makes resolution atomic.

## When the user decides

Pending decisions block only the work declared in their `Scope` field, not all repository work. Read the field before assuming a pending card blocks unrelated tracks, issues, or paths.

The orchestrator (or the user directly):

1. Records the chosen option in the file (e.g., add a `**Decided:** Option A — {brief reason}` line)
2. Adds the date the decision was made (`**Decided on:** YYYY-MM-DD`)
3. **Moves the file** from `docs/decisions/pending/` to `docs/decisions/{YYYY-MM-DD}-{slug}.md` (canonical decisions journal — note the date is the DECISION date, not the original surface date if they differ)
4. References the canonical file from any GH issues or session handoffs that depended on the decision

## What does NOT belong here

- **Multi-week architectural calls** → file as a GH issue with `decision-pending` label. The issue thread IS the deliberation record. Decision Card is the issue body.
- **Trivial choices the orchestrator should make alone** → just decide and act. Don't card every choice — only ones where the user explicitly should weigh in (decolonization-sensitive, foundational, or where multi-agent deliberation surfaced real disagreement).
- **Records of decisions already made** → those go in `docs/decisions/{date}-{slug}.md` directly, no `pending/` step.

## Examples of decisions that DO belong here

- "POC anchor module choice — M10 vs M20" (decolonization-sensitive, surfaced via deliberation)
- "module_type architecture — categories + branching strategy" (foundational, agents disagreed on category boundaries)
- "Writer choice for batch — Gemini-tools vs claude-tools" (project-priority weighting + budget trade-off)
- "Should we delete or deprecate scripts/X.py" (when ab discuss surfaced a real consequence)

## Examples of decisions that do NOT belong here

- "Merge this clean PR" — orchestrator merges per memory rule #0H
- "Delete a leftover file Gemini flagged" — orchestrator fixes inline
- "Rebase a branch onto main" — mechanical, no user input needed
- "Choose between two tactically equivalent code structures" — Codex/Gemini decide during implementation
