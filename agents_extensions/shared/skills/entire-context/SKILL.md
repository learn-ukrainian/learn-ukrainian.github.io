---
name: entire-context
description: Provider-neutral recall over the public body-free context-link index (ADR-018, Phase 2). Invoke when a task needs to find prior public work, explain why a commit or ACP discussion exists, or prepare a bounded handoff capsule for another seat. Works identically for Codex, Kimi, GLM, Claude, and other harnesses — no model-specific semantics, no Entire plugin, no Entire CLI call. Local-only; GitHub, Fleet Comms, Monitor, session streams, rollover, and formal review remain authoritative.
effort: low
---

# Entire context recall (public, body-free)

This skill is the canonical agent-facing contract for the public context layer.
It runs one provider-neutral CLI — `python -m scripts.entire_context` — over the
local context-link projection. It is **supplemental**: it never replaces GitHub,
Fleet Comms, Monitor, session streams, rollover receipts, or formal review, and
it never mutates them.

## Hard privacy and scope rules

- **Body-free only.** Results are locator cards and verified canonical excerpts
  (commit parents/touched paths/timestamps; ACP terminal metadata with
  `content_included: false`). Never request, emit, or persist transcripts,
  prompts, responses, subjects, artifacts, raw captures, secrets, or
  AI-generated summaries.
- **No Entire dependency.** Entire CLI 0.8.42 stays pinned, optional, and
  non-load-bearing. This workflow makes **zero** Entire CLI invocations and
  zero network calls. Do not run `entire` login, search, checkpoint, attach,
  resume, push, or create `refs/entire/*`.
- **Fail closed.** Missing, stale, tombstoned, partial-terminal, unsupported,
  or digest-mismatched evidence is omitted with a machine reason. Never inject
  an omitted item into your context, and never fabricate coverage for a kind
  the resolver reports as `unsupported_kind`.
- **Query hygiene.** Query text is a ranking needle only: at most 256 UTF-8
  bytes, never persisted, never echoed into results.

## Commands

All commands are local and read-only except the two explicit `bootstrap-*`
index commands, which write only to the projection SQLite file.

```bash
# Projection state (body-free aggregate)
.venv/bin/python -m scripts.entire_context status

# Explicit bootstrap/index of real public evidence (idempotent)
.venv/bin/python -m scripts.entire_context bootstrap-git <40-hex-sha> [--repo PATH] [--namespace NS]
.venv/bin/python -m scripts.entire_context bootstrap-acp conversation_<32hex> [--git-sha SHA] [--acp-root PATH]
.venv/bin/python -m scripts.entire_context bootstrap-rollover --agent <agent> --lineage-id <lineage> --rollover-id <rollover> [--rollover-root PATH]

# search-past-work: ranked verified locator cards (<= 10 results, <= 500 scanned)
.venv/bin/python -m scripts.entire_context search --query "<needle>" [--repo PATH] [--acp-root PATH]

# explain-change: typed provenance traversal from an exact seed
.venv/bin/python -m scripts.entire_context explain-change --sha <40-hex>
.venv/bin/python -m scripts.entire_context explain-change --locator-id clink_<64hex>
.venv/bin/python -m scripts.entire_context explain-change --canonical-id <id>

# prepare-handoff: bounded capsule of verified locators/excerpts (<= 5 items, <= 8 KiB)
.venv/bin/python -m scripts.entire_context handoff --locator-id clink_<64hex> [--locator-id ...]
.venv/bin/python -m scripts.entire_context handoff --query "<needle>"
```

Resolution flags: `--repo` (default: cwd) supplies the local git repository;
`--acp-root` or `ENTIRE_CONTEXT_ACP_ROOT` supplies the ACP receipt plane root;
`--rollover-root` or `ENTIRE_CONTEXT_ROLLOVER_ROOT` supplies the rollover
registry state root. Without an ACP root, ACP links fail closed as
`source_missing`; without a rollover root, rollover links fail closed as
`source_missing`. `--db` or
`ENTIRE_CONTEXT_DB` overrides the projection path. `--consumer <label>` may be
passed by any harness; it is validated, never persisted, and never echoed, so
all harnesses receive byte-identical results for identical invocations.
An ACP `--git-sha` join is admitted only when hashing that exact SHA matches
the conversation's canonical correlation digest. Caller-asserted joins fail
closed as `digest_mismatch`.

## Typed resolvers in this slice

| Kind | Resolver | Verification |
| --- | --- | --- |
| `git_commit` | Real | Read-only local git plumbing: parents, touched paths, committer timestamp, author. No commit subject/body. |
| `acp_conversation` | Real | Existing terminal receipt verifier (`verify_discussion_receipt`), metadata-only, `content_included: false`. |
| `rollover` | Real | Existing read-only registry verifier (`rollover_registry.load_record`): strict body-free projection of schema/key, lifecycle state/boundary, sub-lifecycle states, `cleanup_authorized`, timestamps, and non-body routing (stream epic, issue number, lifecycle state). |
| `github_issue` / `github_pr` | Unsupported | No local canonical store verifiable without network; fails closed. |
| `fleet_receipt` / `formal_review` / `monitor_run` | Unsupported | No local canonical store verifiable without protected-rail access; fails closed. |

## How to consume results

1. Prefer exact identifiers when you have them (commit SHA, conversation ID,
   locator ID) — exact canonical ID or SHA matches rank first.
2. Treat every card as a **locator**: read the canonical source itself
   (`git show`, the ACP receipt, the GitHub issue) before relying on details.
   The card's `canonical_digest` proves the locator matches the canonical
   evidence at recall time.
3. Check `omitted` before concluding absence: an omitted card names the
   locator and a machine reason (`source_missing`, `digest_mismatch`,
   `partial_terminal`, `tombstoned`, `unsupported_kind`, `capsule_budget`).
4. A handoff capsule with `"complete": false` intentionally dropped items to
   stay within the item/byte caps; it is still valid JSON and safe to pass on.
5. Ranking is deterministic and Unicode-casefold based with `locator_id` as
   the final tie-break, so identical fixtures give identical results to every
   harness.

## Failure posture

A missing, disabled, or unreadable projection yields a body-free status
payload (`"available": false`) with exit code 0 for read commands — recall is
optional and must never block or mutate your canonical workflow. If recall is
unavailable, continue with the authoritative systems directly.
