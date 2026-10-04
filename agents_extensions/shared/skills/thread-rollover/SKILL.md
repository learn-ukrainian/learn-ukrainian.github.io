---
name: thread-rollover
description: Prepare or resume a durable task rollover, verify continuity, and archive a confirmed predecessor.
---

# Thread Rollover

Use the exact deployed `--agent` and `--harness` for the active runtime. Never
fork, continue, copy provider history, or select a task by title. The repository
owns the fleet-wide `task-identity.v1` envelope, transition plan, and receipts.
An app-capable adapter owns native create/title/archive calls; an unsupported
adapter records the shared carrier fallback and never claims a native rename.
Repo-local Python never writes provider state directly.

## Choose the current phase

Read the relevant procedure before its commands; use repository-root command
paths. Do not load preparation mechanics merely to inspect or resume a packet.

| Current request/state | Read |
| --- | --- |
| Detect, inspect health, or resolve ambiguous packets | [Health and exact detection](references/health.md) |
| Prepare a replacement or repair an interrupted native intent | [Prepare and bind](references/prepare.md) |
| Resume the exact replacement and prove continuity | [Resume and confirm](references/resume.md) |
| Archive a confirmed predecessor or reconcile final cleanup | [Archive proof](references/archive.md) |

Provider-seat canary: Grok and Kimi mint their seat probe while preparing
(`scripts.session_canary.{grok,kimi}_lane mint`; Grok detail in
`docs/runbooks/grok-session-canary.md`), score it from memory on resumption, and
stop through FAIL-HANDOFF below 8/10. This is additional to exact identity binding
and the strict 10/10 continuity proof, never a replacement or a cleanup waiver.
Gemini fails closed: `gemini_lane score` closes the session after a failed score
or blocked hydration, so do not run `gemini_lane` mint or score until an
independently reviewed lease-safe runtime repair lands. A Gemini seat halts the
affected continuation and preserves its handoff and session state; the supervisor
owns disposition. Never bypass the health check, record a canary result that was
not scored, or treat this halt as a core or eligibility change.
Claude and Sonnet use SessionStart/PostCompact; Codex keeps its existing launcher
hydration and never reruns the launcher canary or touches the lease.

Preparation never authorizes cleanup. Exact native identity/title readback and
both continuity proofs must pass before predecessor cleanup. Missing support,
unknown pin state, running tasks, or ambiguous evidence preserve the predecessor.
Never delete leases or infer completion from age, names, or a missing process.
