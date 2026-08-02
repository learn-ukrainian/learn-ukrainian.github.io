---
name: entire-context
description: >
  ALWAYS run at cold start / task intake for non-trivial work (no operator prompt
  required). Provider-neutral body-free context-link recall (ADR-018): status,
  search-past-work, explain-change, prepare-handoff, record-use. Also use before
  consequential design changes, when explaining a commit or ACP discussion, and
  when preparing a handoff. Works for Codex, Kimi, GLM, Claude, Grok, and other
  harnesses. GitHub, Fleet Comms, Monitor, session streams, rollover, and formal
  review remain authoritative. Never skip search on multi-step drives.
when-to-use: >
  session start; cold start; orient; task intake; continue; resume; handoff;
  what happened; prior work; explain commit; ACP discussion; epic drive; before
  dispatch; before design change; entire; entire.io; entire-context; memory
effort: low
---

# Entire context recall (public, body-free)

**Automatic intake:** On any non-trivial task, run `status` + `search` (and
`record-use` when locators inform the plan) **before** prioritization or
dispatch. Do not wait for the operator to say “use Entire.” Skip only for pure
one-line questions or when the module is missing/disabled (note that once).

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

Recall commands are local and read-only. Explicit `bootstrap-*`,
`reconcile-acp`, and `record-use` commands write only to the rebuildable local
projection; `refresh-provider-status` writes only a sanitized local cache.

```bash
# Projection state (body-free aggregate)
.venv/bin/python -m scripts.entire_context status

# Explicit bootstrap/index of real public evidence (idempotent)
.venv/bin/python -m scripts.entire_context bootstrap-git <40-hex-sha> [--repo PATH] [--namespace NS]
.venv/bin/python -m scripts.entire_context bootstrap-acp conversation_<32hex> [--git-sha SHA] [--acp-root PATH]
.venv/bin/python -m scripts.entire_context bootstrap-rollover --agent <agent> --lineage-id <lineage> --rollover-id <rollover> [--rollover-root PATH]
.venv/bin/python -m scripts.entire_context bootstrap-github-issue <number> [--issue-cache PATH] [--repo PATH]
.venv/bin/python -m scripts.entire_context bootstrap-github-pr <number> --head-sha <40-hex-sha> --repository <owner/repo> [--fleet-root PATH] [--repo PATH]
.venv/bin/python -m scripts.entire_context bootstrap-formal-review <review-id> [--fleet-root PATH]
.venv/bin/python -m scripts.entire_context bootstrap-fleet-receipt <request-id> [--fleet-root PATH]
.venv/bin/python -m scripts.entire_context bootstrap-monitor-run <lease-token> [--monitor-root PATH]

# Recover terminal ACP receipts missed by the automatic post-commit callback
.venv/bin/python -m scripts.entire_context reconcile-acp --acp-root PATH

# search-past-work: ranked verified locator cards (<= 10 results, <= 500 scanned)
.venv/bin/python -m scripts.entire_context search --query "<needle>" [--repo PATH] [--acp-root PATH]

# explain-change: typed provenance traversal from an exact seed
.venv/bin/python -m scripts.entire_context explain-change --sha <40-hex>
.venv/bin/python -m scripts.entire_context explain-change --locator-id clink_<64hex>
.venv/bin/python -m scripts.entire_context explain-change --canonical-id <id>

# prepare-handoff: bounded capsule of verified locators/excerpts (<= 5 items, <= 8 KiB)
.venv/bin/python -m scripts.entire_context handoff --locator-id clink_<64hex> [--locator-id ...]
.venv/bin/python -m scripts.entire_context handoff --query "<needle>"

# After verified locators actually informed the task, attest that use explicitly
.venv/bin/python -m scripts.entire_context record-use --task-id <task> --consumer <harness> --purpose <category> --locator-id clink_<64hex> [--locator-id ...]

# Explicit Entire 0.8.42 probe for Monitor's sanitized local cache
.venv/bin/python -m scripts.entire_context refresh-provider-status [--repo PATH]
```

Resolution flags: `--repo` (default: cwd) supplies the local git repository;
`--acp-root` or `ENTIRE_CONTEXT_ACP_ROOT` supplies the ACP receipt plane root;
`--rollover-root` or `ENTIRE_CONTEXT_ROLLOVER_ROOT` supplies the rollover
registry state root. Without an ACP root, ACP links fail closed as
`source_missing`; without a rollover root, rollover links fail closed as
`source_missing`. `--fleet-root`, `--monitor-root`, and `--issue-cache` select
existing local canonical stores for fixtures or operators; otherwise linked
worktrees use the primary shared `batch_state` stores. `--db` or
`ENTIRE_CONTEXT_DB` overrides the projection path. By default every linked
worktree resolves the same primary-checkout `batch_state/entire-context/v1`
projection through Git's common directory. `--consumer <label>` may be
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
| `github_issue` | Real | Fresh `issue_stream_audit.json`: exact open issue plus one unique stream/epic membership. Cache freshness is verification evidence, never locator identity. No body or title. |
| `github_pr` | Real | Completed local formal-review job, matching durable `github_publications` row for the exact head and gate context, plus a local Git commit object. |
| `formal_review` | Real | Completed job; read-only hash-verified sealed verdict strictly parsed and bound again to its job. Exposes only review/repository/PR/head/gate/state/verdict/model/family/harness/attempt/publication state. |
| `fleet_receipt` | Real | Exact terminal Fleet `requests` row only; no invocation specification or messages. |
| `monitor_run` | Real | Exact terminal Agent Process Monitor lease only; no PID or process-create time. |

All resolver source reads are local and read-only. SQLite opens with URI
`mode=ro`; resolvers never migrate, change WAL mode, prune, start a service,
or call GitHub, Fleet, Monitor, Entire, or the network. Missing, malformed,
nonterminal, stale, unpublished, hash-mismatched, or digest-drifted inputs are
omitted fail-closed.

## Product prompt workflow and optional Entire tools

For product-style prompts, invoke the local body-free workflow in this order:
`search` for search-past-work, `explain-change` for an exact provenance path,
and `handoff` for a bounded capsule. Use the `.venv/bin/python` commands above;
they are the canonical recall path.

Native `entire blame --json` is allowed only for local attribution. Prompt-
bearing `entire why`, cloud `entire search`, generated recap, investigate
findings, and Entire review are optional manual tools. They never automatically
enter a canonical capsule. Entire review is supplemental and never satisfies
the Fleet formal-review gate.

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
6. Search delivery is not evidence of use. When verified cards materially
   informed intake, architecture, implementation, explanation, review, or
   handoff, run `record-use` with the exact task, harness, purpose, and locator
   IDs. The body-free idempotent receipt is the only basis for Monitor's
   `use.proven` state.

## Harness semantics

- Entire integrates with the **host harness**, not each model label. Kimi or
  GLM running inside Claude Code use the installed `claude-code` integration;
  those models running inside OpenCode use the installed `opencode`
  integration.
- Codex CLI and Codex Desktop first use the installed native `codex`
  integration and the same project hooks. Do not invent a `codex-gui` agent.
- Add an external `entire-agent-<harness>` adapter only after a source-blind
  canary proves that the actual unsupported harness has no native capture
  path. A model name alone is never evidence that an adapter is required.

## Failure posture

A missing, disabled, or unreadable projection yields a body-free status
payload (`"available": false`) with exit code 0 for read commands — recall is
optional and must never block or mutate your canonical workflow. If recall is
unavailable, continue with the authoritative systems directly.
