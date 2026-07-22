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
claimed the stream lease — do **not** open or resume it yourself). Mint your session
canary: `.venv/bin/python -m scripts.session_canary.<model>_lane mint --epic <epic>`.

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

### 5. Settle-loop (never poll by hand)
Watch the task's `batch_state/tasks/<id>.json` `status` with the **Monitor** tool.
Terminal vocab (match `scripts/delegate.py`): **`done` = SUCCESS** (NOT "completed");
other terminal/attention states: `failed | timeout | rate_limited | cancelled |
crashed | dry_run` (dry_run is terminal, not success) + `needs_finalize`. Emit on any
status NOT in `{spawning, running, ""}`. The task file is truth; `/api/delegate/active`
can omit live tasks. **Before declaring a dispatch dead:** `gh pr list --state open`
first, then check the worktree for finished-but-unpushed work.

### 6. Cross-family review gate (load-bearing — discussion ≠ review)
A review of record is **independent and cross-family** (outside the author's model
family; never self-review, never same-family). Route it:
```bash
.venv/bin/python -m scripts.ai_agent_bridge review-pr --reviewer <cross-family-lane>   # claude|glm|codex|...
.venv/bin/python -m scripts.ai_agent_bridge publish-review-verdict ...                 # publish the sealed verdict
```
Pick the reviewer family from the served reviewer-seat rule; the writer's family is
never eligible. Read the review CONTENT (not just pass/fail), apply the deltas, re-probe
gate-driving data yourself before trusting "verified".

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
End the session on canary FAIL-HANDOFF, not on a compact count. Write your handoff to
both surfaces while the plane is in dual-write phase.

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
- **After the infra lane flips the cutover:** the plane becomes authoritative; the file
  fallback is dropped. That is a one-line config change (`fleet_communications.yaml`),
  not a rewrite of this skill.
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
