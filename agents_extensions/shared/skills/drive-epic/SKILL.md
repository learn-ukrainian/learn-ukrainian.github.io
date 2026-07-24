---
name: drive-epic
description: Model-agnostic orchestrator playbook for driving ONE epic/track lane end-to-end over the fleet-comms message plane. Invoke this when you are launched as an epic/track driver (Grok, Sonnet-5, Gemini/AGY, Kimi, or Claude) via a start-<model>.sh --epic launch and told to "drive this epic". Teaches the METHOD — topology → route → dispatch → settle → cross-family review → merge → handoff — and defers all live roster/routing DATA to /api/rules and model_catalog.yaml. Not for main-orchestrator cold-start (that has its own hook) and not for writing a single module (use $track-completion).
effort: xhigh
---

# Drive an epic lane

You were launched to **drive one epic/track lane** (`SESSION_EPIC` is set). You are
**NOT** the main orchestrator. This skill is the portable playbook every non-Claude
driver — and Claude when driving a track — follows so orchestration behaves the same
regardless of which model is in the seat.

**Golden rule of this skill: it teaches the _method_, never the _roster_.** Who is in
which lane, which model fits which task, and the in-flight caps are **live data** that
change; always read them fresh from the served rules and catalog, never from memory:

- `GET http://127.0.0.1:8765/api/rules` — model-assignment (routing SSOT), review-seat
  economics, cross-family pairing. Served first; supports `If-None-Match`.
- `scripts/config/model_catalog.yaml` — machine-enforced quality floors + ordered peer
  tiers per task-risk.
- `docs/best-practices/agent-activity-matrix.md` §2/§2b — roster + no-idle capacity routing.

If any claim you are about to make (a lane name, a cap, a word/stress/morphology fact,
a gate status, a count) is not in fresh tool output, **STOP and run the tool** — every
verifiable claim is tool-backed (deterministic-over-hallucination).

---

## The loop (run it every cycle)

### 0. Orient
```bash
curl -sS --max-time 2 "http://127.0.0.1:8765/api/orient?lean=true" || true
.venv/bin/python -m scripts.fleet_comms plane-status        # message-plane mode/parity
```
Know your `SESSION_EPIC`, your stream, and your handoff slot (the launcher already
claimed the stream lease — do **not** open or resume it yourself). Establish your
session-health signal **by seat**: **grok / gemini / kimi** have a canary lane —
`.venv/bin/python -m scripts.session_canary.{grok,gemini,kimi}_lane mint --epic <epic>`;
**Claude / Sonnet** have **no** canary lane and use the native SessionStart / PostCompact
hook chain + thread-handoff instead (do not call a non-existent `<model>_lane`).

### 0a. Required live-driver inbox drain — cycle start
At the start of **every** cycle, inspect this driver's legacy inbox. The live loop —
not a detached `process-*` / `ask-*` worker — must read and apply every message marked
`unread` or `read-but-not-live-consumed`, then record that consumption explicitly:
```bash
.venv/bin/python -m scripts.ai_agent_bridge inbox --for "$SESSION_HANDOFF_AGENT"
.venv/bin/python -m scripts.ai_agent_bridge ack --consumed-by-live-driver <message-id> [<message-id> ...]
```
Never use a plain `ack` for messages this live loop has consumed: plain acknowledgement
also records one-shot/headless processing and is not delivery proof for the live driver.

### 0b. Optional Monitor inbox-watcher wakeup — cold start only

At cold-start, **if your harness has a Monitor-equivalent**, invoke it once with that
harness's `persistent`/timeout option, pointed at this one shell command:

```bash
scripts/ai_agent_bridge/inbox_watch.sh "$SESSION_HANDOFF_AGENT"
```

This is a **wakeup signal only**: each stdout line says that an unconsumed legacy
message exists, with its id, sender, request id, and a bounded preview. It never reads
the full body into your context and never marks a message consumed. You still must run
the existing required `0a` / `4a` / `5a` / `8a` inbox-drain steps to read, apply, and
explicitly live-consume everything the signal points at; those steps remain the
universal fallback for every seat, watcher or not.

Direct confirmation exists only for **Claude Code, Gemini/AGY, and Grok CLI**. For any
other harness, ask the running agent directly whether it has an equivalent before using
one; do not infer it from documentation or `--help`. Stop a running watcher cleanly
with `scripts/ai_agent_bridge/inbox_watch.sh --stop "$SESSION_HANDOFF_AGENT"`; if a
crashed process leaves a stale pidfile, the operating system releases its advisory lock
and the next watcher replaces the recorded pid safely.

### 1. Read topology + metrics (don't hold state — query it)
```bash
.venv/bin/python -m scripts.fleet_comms metrics        # efficiency metrics (no content)
.venv/bin/python -m scripts.fleet_comms backlog        # pending/dispatched delivery
.venv/bin/python -m scripts.fleet_comms dead-letters   # stuck deliveries
```
Fleet-comms externalizes topology + usage so you decide against fresh state, not a
stale in-context snapshot. For per-lane budget health:
`scripts/delegate.py --check-budget` (+ `/api/state/routing-budget` for subscription lanes).

### 2. Pick the next unblocked action
Source of next work: your epic's stream tail / handoff, open GH issues for the epic, and
the build/review queue. **Step 0 of any dispatch:** `gh pr list --state all --search
"<issue-nr>"` by issue reference (an open issue ≠ unfixed; a sibling PR may already
carry it). If nothing genuinely fits a free lane, log it and leave it idle — never
manufacture busywork (quality > utilization).

### 3. Route by model × harness fit
Decide the lane from `/api/rules` + `model_catalog.yaml`, **never** from the provider
name. Respect the live caps (in-flight ceilings), the language-lane restriction
(UK authoring / linguistic / content review route only to the sanctioned language lanes
per the served rules), folk carve-outs (cross-family only), and the judge-seat rules.
On limit: note the substitution and reroute per the fallback table — never block on one lane.

### 4. Dispatch
`scripts/delegate.py dispatch --agent <lane> --worktree ...` with a numbered brief
(worktree → work → tests → ruff → conventional commit → push → PR → **no auto-merge by
the worker**) and the `#M-4` evidence preamble (each claim + its deterministic tool +
quoted raw evidence). Classify the task and pass the research flags
(`--research-role/-task-family/-track/-owned-path`). Stagger same-lane spawns ~10s.

### 4a. Required live-driver inbox drain — immediately before dispatch
Immediately before each dispatch, repeat the drain so new instructions or a reply cannot
be missed between routing and worker launch. Read and apply every `unread` or
`read-but-not-live-consumed` entry before dispatching, then run:
```bash
.venv/bin/python -m scripts.ai_agent_bridge inbox --for "$SESSION_HANDOFF_AGENT"
.venv/bin/python -m scripts.ai_agent_bridge ack --consumed-by-live-driver <message-id> [<message-id> ...]
```

### 5. Settle-loop (never poll by hand)
Watch the task's `batch_state/tasks/<id>.json` `status` with the **Monitor** tool.
Terminal vocab (match `scripts/delegate.py`): **`done` = SUCCESS** (NOT "completed");
other terminal/attention states: `failed | timeout | rate_limited | cancelled |
crashed | dry_run` (dry_run is terminal, not success) + `needs_finalize`. Emit on any
status NOT in `{spawning, running, ""}`. The task file is truth; `/api/delegate/active`
can omit live tasks. **Before declaring a dispatch dead:** `gh pr list --state open`
first, then check the worktree for finished-but-unpushed work.

### 5a. Required live-driver inbox drain — after settle
Once the settle-loop reaches its decision point, drain again before choosing the next
action. Read and apply every `unread` or `read-but-not-live-consumed` entry, then run:
```bash
.venv/bin/python -m scripts.ai_agent_bridge inbox --for "$SESSION_HANDOFF_AGENT"
.venv/bin/python -m scripts.ai_agent_bridge ack --consumed-by-live-driver <message-id> [<message-id> ...]
```

### 6. Cross-family review gate (load-bearing — discussion ≠ review)
A review of record is **independent and cross-family** (outside the author's model
family; never self-review, never same-family). Route it:
```bash
# PR number is REQUIRED and positional (omitting it exits with a usage error):
.venv/bin/python -m scripts.ai_agent_bridge review-pr <PR_NUMBER> --reviewer <cross-family-lane>   # e.g. review-pr 5632 --reviewer codex
.venv/bin/python -m scripts.ai_agent_bridge publish-review-verdict ...                             # publish the sealed verdict
```
Pick the reviewer family from the served reviewer-seat rule; the writer's family is
never eligible. For a hard / non-routine change, escalate the seat with
`--model gpt-5.6-sol` (or `claude-fable-5`) `--effort xhigh`. Read the review CONTENT
(not just pass/fail), apply the deltas, re-probe gate-driving data yourself before
trusting "verified". A review request is not a passive notification: after invoking
`review-pr <PR_NUMBER>`, the requester owns its request state and must explicitly poll
it on each subsequent cycle with:
```bash
.venv/bin/python -m scripts.ai_agent_bridge asks --task-id review-pr-<PR_NUMBER>
```
Wait for that request to show `replied`; treat `sent`, `processing`, `timed-out`, or
`failed` as its actual state and act on it. Do not assume a disconnected reply will
surface in the live driver's context.

### 7. Merge discipline
PRs only — never commit or merge to `main` directly. **Arm auto-merge the moment the
review gate passes AND blocking CI is green:**
```bash
gh pr merge --auto --squash --delete-branch
```
Never arm on a **draft** and never merge ahead of the review verdict. Blocking CI red →
never `--admin`-bypass. After merge: delete remote branch, `git worktree remove --force`
(worktree BEFORE local branch), sweep stale refs. A track/infra driver **self-merges its
own lane's PR** after the cross-family gate + green CI (lane model — there is no promoting
orchestrator). Flag another lane's PR with `needs=merge` rather than merging it.

### 8. Handoff — dual-write, cutover-aware (see §Fleet-comms state below)
End the session on your seat's handoff signal (canary FAIL-HANDOFF for grok/gemini/kimi;
the SessionStart / thread-handoff for Claude/Sonnet), not on a compact count. Keep the
file handoff current — it stays authoritative through every plane mode (below).

### 8a. Required live-driver inbox drain — before handoff
Immediately before writing or signalling handoff, make one final live-loop drain. Read
and apply every `unread` or `read-but-not-live-consumed` entry, then run:
```bash
.venv/bin/python -m scripts.ai_agent_bridge inbox --for "$SESSION_HANDOFF_AGENT"
.venv/bin/python -m scripts.ai_agent_bridge ack --consumed-by-live-driver <message-id> [<message-id> ...]
```
Record any action or unresolved request in the authoritative file handoff after this
drain; never claim the handoff is complete because a one-shot worker acknowledged it.

---

## Fleet-comms state — dual-aware, do not race the cutover

The message plane exists but the `dual_write` cutover is an **operator/advisor-gated
flip owned by the infra/harness lane** (parity receipt → approved enable). Until it
flips, **file handoffs remain authoritative** (`session_streams --help` itself says: "do
not use it to cut over or retire file handoffs").

- **Check first:** `.venv/bin/python -m scripts.fleet_comms plane-status` and
  `.venv/bin/python -m agents_extensions.shared.session_streams dual-write-status`.
- **While `mode: off` / dual-write:** coordinate via the plane where available AND keep
  the file handoff current (`.claude/<epic>-epic/*DRIVER-HANDOFF.md` where the epic uses
  one — gitignored local state; or `docs/session-state/` for infra). Successor-claim
  diagnostics: `session_streams handoff-status` / `handoff-claim` (#5530).
- **Plane modes are only `off → shadow → dual_write`** (`plane-status`). In **all** of
  them the file handoff stays authoritative — `dual_write` is shadow/mirror, **not**
  cutover, and there is **no implemented post-cutover authority state** today. **Never
  drop the file handoff on your own.** Retiring file handoffs is a future infra step
  gated on an implemented authority signal the plane does not yet expose — not a config
  edit a driver makes.
- **Never** flip the plane, enable retention apply, or invent a competing comms design
  from this skill — those are the infra lane's gated actions.

---

## Per-model capability delta

Same playbook; each seat adjusts on the axes the fleet has measured. This is the ONLY
model-specific section — everything above is identical across seats.

| Seat | Delta |
| --- | --- |
| **Grok 4.5** | Higher hallucination rate than peers → enforce tool-backed-only **harder**: never assert a word/stress/gate/count/SHA without the raw tool output quoted. 500K window — lean on plane/metrics queries, don't try to hold fleet state in context. Never take a judge seat. |
| **Sonnet-5** | You are authority-capable (near-Opus judgment, 1M window) → make the judgment call and escalate **less**; still escalate the genuinely architecture/process class (below). CF reviews you route must go to a **non-Anthropic** family (you are Anthropic-family — avoid self/same-family review). |
| **Gemini / AGY (gemini-3.6-flash-high)** | Harness/infra scope. MCP-leading tool use + 1M window + low cost = ideal infra driver. **Do not claim curriculum content lanes.** Route UK-language work to the sanctioned language lanes, not to yourself. |
| **Kimi K3** | Frontier coder/reviewer + cross-family escalation authority (independent of Anthropic & OpenAI). `max-effort-only` makes a continuous loop costly — drive when assigned, else stay a reviewer/escalation seat. |
| **Claude (when driving a track)** | Reserve the Opus seat for the hardest judgment + the CF review of record; prefer Sonnet-5 for routine track driving so Opus quota stays free. |
| **Codex / GPT-5.6 Terra** | Named alternate only for harness / infra (`epic:4707`) and the independent DevOps stream (`epic:5703`). The launcher injects the HydrationCapsuleV1 cold-start board and binds at most one exact fresh CLI rollover; stop on any SessionStart setup error. Codex has no Monitor-equivalent watcher, so use bounded foreground waits and escalate hard judgment to Sol. |

---

## Escalate — do NOT decide these solo

Route to the **operator + advisors (Fable, Sol)** — never resolve from the loop:

1. Any **architecture / layout / process** change.
2. A **contested CF verdict** (reviewer and author disagree, or two reviewers split).
3. A **fragile-fix** situation — challenge the premise, root-cause it, then escalate the
   design if the right layer is unclear.
4. A **high-risk route** that would trip the `risk_quality_floor` in `model_catalog.yaml`.
5. Anything requiring **repo-wide safety** interruption of another lane (generated
   artifacts, linter/Python-version bumps, cross-track architecture conflict).

Enforce the risk floor **on yourself**, not only on the work you dispatch. Gates passing
is necessary, not sufficient — verify the real artifact renders/runs before "ready".

## This skill is NOT

- A replacement for the served rules (`/api/rules`) — it points to them; it never
  restates the live roster.
- The main-orchestrator cold-start (that has its own SessionStart hook / handoff chain).
- A single-module writer (use `$track-completion`).
- Authority to flip the plane cutover, self-merge a fleet-wide process change, or
  self-review your own dispatched work.
