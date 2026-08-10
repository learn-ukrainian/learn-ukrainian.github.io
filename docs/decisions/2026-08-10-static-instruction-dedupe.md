# Design Note: Static instruction dedupe for agent cold starts

- **Date:** 2026-08-10
- **Issue:** #6449
- **Status:** implemented
- **Scope:** `AGENTS.md` static injection for Codex-family consumers only

## Context

`AGENTS.md` was 30,863 UTF-8 bytes (550 lines) and is injected before Codex
work. The full canonical policy is already served at `/api/rules` and remains
available as ordered local fallback sources. Duplicating the full rule layer in
the static file spends context without improving the source of truth.

`CLAUDE.md` is deliberately out of scope: headless `claude -p` may not fetch
the rules API, and its existing inline operator-contract digest remains intact.

## Decision

Use a tiered static digest for `AGENTS.md` with a hard 9 KiB UTF-8 budget. Keep
the 14-item operator-contract digest and the minimum non-skippable safeguards
needed by AGENTS-only/offline Codex consumers: worktree isolation, deployment
source order, interpreter, protected configuration, generated-artifact and
test integrity, secret handling, attribution, PR/cross-family review, Entire
recall, and bounded delegation.

The digest names both the live `GET /api/rules?format=markdown` source and the
local `agents_extensions/shared/rules/_load-via-api.md` fallback. Detailed or
dynamic policy remains in the rules API and its ordered sources; this change
does not create a second complete rule system.

## Alternatives rejected

- **Generated digest:** unnecessary build and deployment surface for this
  bounded reduction; the byte ceiling and required-clause test catch drift.
- **Pointer-only file:** unsafe for AGENTS-only consumers when the API is
  unavailable, because critical negative constraints become skippable.
- **Per-harness redesign:** outside this issue and would affect headless Claude
  and other launchers without evidence that their injection behavior changes.

## Review and verification plan

The deterministic wiring test enforces the UTF-8 byte ceiling and required live,
offline, and safety clauses. The existing contract tests continue to require the
operator digest. An independent Gemini-family design critique selected the same
tiered approach; the requested Gemini 3.1 Pro lane was unavailable through ACP,
so the documented Gemini 3.6 Flash substitution was used. Exact-head
cross-family PR review remains required before any merge.
