# Architecture Decision Records (ADRs)

Permanent records of architectural decisions for the learn-ukrainian curriculum project. These are distinct from `docs/decisions/` — that directory holds **ephemeral, expiring** decisions (default 90-day expiry); this directory holds **permanent** architectural choices that defined the shape of the system.

## What belongs here

An ADR should capture:

- **Context** — what situation prompted the decision
- **Decision** — what we actually chose
- **Alternatives considered** — what else we looked at and why we rejected it
- **Consequences** — trade-offs accepted, downstream impacts
- **Status** — `accepted`, `superseded by ADR-NNN`, `deprecated`

The threshold for writing an ADR: **would a new engineer need to know this to understand why the codebase looks the way it does?** If yes, write one. If no, the `docs/decisions/` journal is the right place.

## Index

| ID  | Title                                     | Status   |
|-----|-------------------------------------------|----------|
| [ADR-001](adr-001-v6-pipeline.md) | V6 pipeline architecture — skeleton → write → review loop | Accepted |
| [ADR-002](adr-002-model-tiering.md) | Model tiering — per-phase model selection | Accepted |
| [ADR-003](adr-003-activity-system-v2.md) | Activity system v2 — YAML → JSX renderers | Accepted |
| [ADR-004](adr-004-agent-runtime.md) | Unified agent runtime — single adapter layer for Claude/Gemini/Codex | Accepted |
| [ADR-005](adr-005-wiki-knowledge-base.md) | Wiki knowledge base — pre-compiled articles replace live RAG for seminar writes | Accepted |

## Template

Copy `adr-template.md` when writing a new ADR. Number sequentially (ADR-006, ADR-007, ...). Never reuse a number, even for a superseded ADR — update the status of the old one and write a new one that references it.

Short format is fine. One page is better than five. The goal is permanent record, not exhaustive documentation.
