# Public source Entire pilot

This receipt onboards `learn-ukrainian/learn-ukrainian.github.io` as a source
repository for Entire 0.8.42 capture.

Checkpoint bodies are stored only in the private
`learn-ukrainian/entire-checkpoints-private` repository. The public product
origin must retain zero `entire/*` refs and zero session bodies. Entire remains
optional and non-authoritative; GitHub, Fleet Comms, Monitor, rollover, leases,
and formal review remain authoritative.

The committed `.entire/settings.json` is the body-free project binding Entire.io
uses to locate the separate checkpoint repository. The canonical generated
agent configuration installs native `codex` and `claude-code` hooks, while the
tracked OpenCode plugin installs native `opencode` lifecycle capture.

Entire integrates with the host harness, not a model label:

- Codex CLI and Codex Desktop use the same `codex` project hooks.
- Kimi or GLM hosted inside Claude Code use `claude-code` hooks.
- Kimi or GLM hosted inside OpenCode use the OpenCode plugin, which records the
  actual `modelID` reported by OpenCode.

Do not run `entire agent add codex`, `entire agent add claude-code`, or
`entire agent add opencode` over the deployed project configuration. The 0.8.42
JSON installers drop project timeout/status metadata, while its stock OpenCode
plugin requires the tracked `entire-exit.ts` termination companion for
OpenCode 1.17.13. Change the canonical sources
under `agents_extensions/`, run the normal worktree/PR/review deployment
workflow, and keep the onboarding contract tests green. A separate
`entire-agent-<harness>` adapter is justified only by a failed source-blind
native-host canary.

The public issue receipt in #6165 records the checkpoint identifier, source
commit, private destination ref, leakage verdict, retry result, and authenticated
Entire activity result without reproducing a prompt, response, transcript, or
generated summary.

Before rollout, run
`.venv/bin/python scripts/entire/validate_checkpoint_routing.py` to prove that
the product setting and egress allowlist still name one identical destination.

The deployed source commit must carry `Entire-Checkpoint` as a real Git trailer.
Escaped newline text is not a trailer and will not enter Entire's activity index.

## Product workflow boundary

Product-style prompts use the local body-free context workflow: search-past-work,
explain-change, and prepare-handoff through `.venv/bin/python -m
scripts.entire_context`. These commands read local verified projections and
produce locator cards or bounded capsules; they do not invoke Entire or the
network.

The operator-authorized private mode is declared in
`.entire/private-recall.json`. Before a prompt-bearing native operation,
`.venv/bin/python -m scripts.entire.private_mode_preflight` proves the GitHub
repository is private, the public origin has zero Entire branches, the private
checkpoint ref exists, authentication works, both mirrors are ready and expose
an operator-only Entire ACL, and the CLI remains pinned. The public GitHub
source remains public, but its Entire mirror is not pullable by other Entire
users. A green receipt permits repository-scoped native search,
metadata or task-required full explain, static recap, and local
dispatch/handoff. The accountable root may consume results in its private task
context. They never automatically enter a shared capsule or public GitHub
evidence, and external disclosure requires operator review. Entire review is
supplemental and never satisfies the Fleet formal-review gate.

The 2026-08-02 source-blind canary proved: authenticated Entire activity saw
eight checkpoints across the public/private source repositories; the public
branch listed three checkpoints; exact checkpoint explain returned a
metadata-only JSON envelope; and static recap returned non-empty output without
printing its body. Source-scoped cloud checkpoint search was reachable but
returned zero checkpoint/session matches, while cloud dispatch was unavailable
(source-repository 404 followed by private-target rate limiting). Local native
full explain is now proved readable without emitting its body, so exact private
session continuity does not depend on cloud search quality. Empty cloud search
and provider rate limits remain truthful optional-provider states, not
canonical workflow failures.

The typed local resolver inventory is deliberately narrow: an open GitHub issue
must have exactly one fresh issue-stream membership; a GitHub PR needs a
completed local formal-review job, matching durable publication receipt, and
local head commit; formal review requires a hash-verified sealed verdict; Fleet
and Monitor require exact terminal receipts. Resolver reads use existing local
caches only, including SQLite URI `mode=ro`; they do not migrate, change WAL,
prune, start services, or contact GitHub, Fleet, Monitor, or Entire.
