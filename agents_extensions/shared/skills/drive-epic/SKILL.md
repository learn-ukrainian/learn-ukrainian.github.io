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
which lane, which model fits which task, and the current width (CodexBar pace/reserve +
disk headroom, not a fixed cap) are **live data** that change; always read them fresh from
the served rules and catalog, never from memory:

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

### 0c. Hramatka epic — dual-repo queue (epic #4542 only)

If `SESSION_EPIC` is Hramatka (public #4542), the priority/ownership queue is
private BOARD `learn-ukrainian-infra-private#349`, not the public epic body. Cold-start
read order: **private #349 → private open PRs → public PRs linked from #4542 only.**
Public #4542 is charter + bare pointer — never generate or mirror a public checklist
from the private board (leak + dual-write). GitHub issue/PR state in either repo
remains the factual SSOT for open/closed; #349 is the priority queue, not a duplicate
status feed. Operator-only host mutation (private #360, #212) is **ESCALATE**, not
solo action, on missing GO. If #349 and any other queue view disagree, **#349 wins** —
correct the other view the same session. Full contract:
`docs/runbooks/hramatka-driver-queue.md`.

Before a new dispatch, scope, or PR, run `scripts.fleet.hramatka_scope_gate`
as specified in that runbook; only `ALLOW` permits the new action.

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

### 2a. NO FABRICATED DONE (binding all epic drivers)

- Never invent acceptance thresholds the operator, issue, or epic goal did not set.
- Never declare a goal done while measured residual remains in the same mandate unless
  tools prove it impossible or the operator accepted it on the issue.
- Never end with "when you want" or an "optional next" for in-scope residual — dispatch it.
- Never relabel unfinished work as an intentional skip without issue text or tool proof.
- Before "done" or handback, quote the tool residual count; `residual > 0` requires a
  next dispatch in the same session.

### 3. Route by model × harness fit
Decide the lane from `/api/rules` + `model_catalog.yaml`, **never** from the provider
name. Respect the live caps (in-flight ceilings), the language-lane restriction
(UK authoring / linguistic / content review route only to the sanctioned language lanes
per the served rules), folk carve-outs (cross-family only), and the judge-seat rules.
On limit: note the substitution and reroute per the fallback table — never block on one lane.

### 3-routing. Mandatory ROUTING_CARD_V1 + breadth (operator GO 2026-08-06)

**Binding full text:** `agents_extensions/shared/rules/fleet-driver-routing.md` (served at
`/api/rules` after model-assignment).

Before **every** implement `delegate.py dispatch`:

1. Emit a **ROUTING_CARD_V1** (handoff / issue / `batch_state/` receipt) with:
   `tier` (authority|practical|heap) · `model_x_harness` · `why_this_tier` ·
   `advisor_packet` (required if tier=heap) · `owned_paths` · `acceptance_cmd` ·
   ≥2 `alternatives_considered` · `parallel_free_seats`.
2. **Default bounded work:** Fable or Sol **brief** → heap/practical **worker(s)** —
   not a Sonnet/Terra fixation solo. Heap without advisor packet is a process defect.
3. **Fable path:** native `claude-fable-5` or Cursor pin to Fable; do not spend Fable on
   lockfiles / pointer / smoke jobs.
4. After ≥3 implement dispatches this session, require ≥2 agents **and** ≥2 tiers **or** a
   written `NOTE: fleet_breadth` with tool-backed blockers.
5. Before handoff, run and attach:
   ```bash
   .venv/bin/python -m scripts.fleet.driver_breadth_report --initiator "$SESSION_HANDOFF_AGENT" --since-hours 24
   # optional hard check:
   .venv/bin/python -m scripts.fleet.driver_breadth_report --initiator grok --since-hours 24 --enforce
   ```

Fixation on one practical seat while free lanes sit idle = utilization failure (same
family as fleet-first / no-solo for Grok).

### 3a. Pre-dispatch outcome adequacy (required before substantive phase/epic kickoff)

Freeze the exact prompt before presenting or routing it. Record its SHA-256, user-visible
outcome, real-world or source denominator, non-goals, role map, independent held-out evaluation,
stop/residual policy, and completion vocabulary. For high-stakes domain work, obtain a
domain-fit review and a distinct adversarial scope/circularity critique; for smaller
consequential work, obtain at least one fast critic. A genuinely trivial bounded prompt is
explicitly exempt. The prompt author counts as neither reviewer. Choose these roles from live
`model-assignment.md` routing, not a
permanent reviewer identity; collect explicit checklist verdicts/findings and reconcile them
before dispatch.

Re-review after a material change to outcome, scope, denominator, role map, acceptance
criteria, or independent evaluation. A non-goal that shrinks the actual mission needs
operator/advisor approval. Prompt review is pre-dispatch quality control only: it never
replaces exact-head implementation review or the cross-family PR review gate. Discovery,
seeds, prototypes, schemas, transport checks, and self-authored canaries may prove research or
engine readiness, never product completion. On handback, name the verified user-visible outcome,
denominator, held-out proof, and residual gap. For normative language evidence, establish the
source's pedagogical or evidential role before consuming an occurrence.

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
crashed | dry_run` (dry_run is terminal, not success) + `needs_finalize | no_deliverable`. Emit on any
status NOT in `{spawning, running, ""}`. The task file is truth; `/api/delegate/active`
can omit live tasks. **Before declaring a dispatch dead:** `gh pr list --state open`
first, then check the worktree for finished-but-unpushed work. **After terminal status,**
run `.venv/bin/python -m scripts.fleet.post_task_reap --task-id <id>` (dry-run by default;
pass `--apply` to reap the bound dispatch worktree).

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
.venv/bin/python -m scripts.ai_agent_bridge review-pr <PR_NUMBER> --reviewer <cross-family-lane>
.venv/bin/python -m scripts.ai_agent_bridge publish-review-verdict ...                             # publish the sealed verdict
```
Pick the reviewer family and capability from the served reviewer-seat rule; the writer's
family is never eligible. For a hard / non-routine change, record the live role selection
and concrete `--override-reason`; do not hard-wire a reviewer identity in this skill. Read the review CONTENT
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
never `--admin`-bypass. A track/infra driver **self-merges its own lane's PR** after the
cross-family gate + green CI (lane model — there is no promoting orchestrator). Flag
another lane's PR with `needs=merge` rather than merging it.

### 7a. Post-merge cleanup is mandatory (binding — operator 2026-08-07)

**A squash-merge is not done until cleanup proves free of that PR's residue.** Chat
promises do not bind; this section does. Leaving worktrees / ACP review runtimes /
`/tmp` formal-review snaps after merge is a process defect (ENOSPC / disk full is the
known failure mode). Do not start the next formal `review-pr` or large dispatch until
cleanup for the just-merged PR is complete.

**Order after `gh pr view <N>` shows `MERGED` (or auto-merge lands):**

1. **Confirm** — `gh pr view <N> --json state,mergedAt,mergeCommit` (quote SHA when
   handoff needs it).
2. **Worktree first** — `git worktree remove --force .worktrees/dispatch/<agent>/<task>`
   (and any other worktree still on that PR branch). Never leave a branch checked out
   that blocks branch delete.
3. **Branches** — delete local branch if present; ensure remote is gone
   (`--delete-branch` on merge, else `git push origin --delete <branch>`); `git fetch
   --prune`; `git worktree prune`.
4. **Review / CF residue for that PR** (reap only when no live process holds the path):
   - `.worktrees/dispatch/acp/runtime-review-<PR>*` — `git worktree unlock` if locked,
     then `remove --force` (or `rm -rf` if already unregistered)
   - `/tmp/lu-cf-clean/`, `/tmp/lu-review-*`, `/tmp/lu-pr*` tied to that PR or finished
     formal snapshots — sealed snaps are often **read-only**: `chmod -R u+w` then
     `rm -rf`
   - runtime tmp under `$TMPDIR/learn-ukrainian/<task-id>*` if present
   - stray worktree `.venv` if a worker created one
5. **Optional sweeper** — not a substitute for step 4:
   ```bash
   .venv/bin/python -c "from scripts.review.isolation import sweep_review_temp_orphans; print(sweep_review_temp_orphans())"
   ```
6. **Prove** — `df -h /` and `git worktree list` must show no zombie path for that PR.
   Record free space in the file handoff when disk was tight this session.

**Do not** treat `gh pr merge --auto --squash --delete-branch` alone as closeout. **Do
not** leave locked ACP review worktrees for finished reviews. **Do not** run another
formal snapshot provision while disk is near full without reaping first.

### 8. Handoff — dual-write, cutover-aware (see §Fleet-comms state below)
End the session on your seat's handoff signal (canary FAIL-HANDOFF for grok/gemini/kimi;
the SessionStart / thread-handoff for Claude/Sonnet), not on a compact count. Keep the
file handoff current — it stays authoritative through every plane mode (below).

On a Hramatka epic (#4542) drive, before declaring the handoff verified-clean run
`.venv/bin/python -m scripts.fleet.hramatka_hygiene_check` — only exit 0 is a pass;
exit 2 (`unknown`, GitHub unreachable) is never a clean handoff either (`docs/runbooks/hramatka-driver-queue.md`).

**Skill source of truth is git, not deploy trees.** Edit only
`agents_extensions/shared/skills/drive-epic/SKILL.md` (this file). Never implement or
“fix” process in `.claude/skills/` or other deploy-rsync targets — those copies are
overwritten on the next agents_extensions deploy and are not durable.

**Entire dual-write (Option A — operator GO 2026-08-02; file remains SSOT):** on every
session handoff, also project public continuity into entire-context. This is
**supplemental** (ADR-018): body-free locators only; never store residual narratives,
task ids, or OPSEC-sensitive prose only in Entire; never treat Entire as handoff
authority or retire the file on your own.

Durable sinks for the dual-write (not private deploy trees):

| Sink | What to write | Survives |
| --- | --- | --- |
| **File handoff** (local operational SSOT; gitignored `.claude/<epic>-epic/*` or `docs/session-state/` when the epic uses a tracked pointer) | Next queue, residual narrative | Local session / tracked pointer as applicable |
| **entire-context projection** (`batch_state/entire-context/…` via CLI) | `bootstrap-git` + capsule via `handoff` + `record-use` | Rebuildable local projection |
| **Fleet-comms channel** | Issue/PR numbers only | Plane authority |
| **GitHub issues** | Residual / next work | Public queue SSOT |

```bash
# 1) Index merge SHAs from this drive (idempotent) — writes the local projection
.venv/bin/python -m scripts.entire_context bootstrap-git <40-hex-sha>   # repeat per merge

# 2) Body-free capsule to stdout (≤5 items). Optional: --locator-id clink_… from bootstrap.
#    Do NOT treat a tee into .claude/ as durable process storage (deploy-wiped).
#    Optional scratch only: batch_state/ (gitignored runtime), never skills trees.
.venv/bin/python -m scripts.entire_context handoff --query "<epic keywords>"

# 3) Attest consumption when locators informed the handoff
.venv/bin/python -m scripts.entire_context record-use \
  --task-id <epic-or-stream-id> --consumer <harness> --purpose handoff \
  --locator-id clink_…   # repeat up to the locators used

# 4) Fleet receipt: issue/PR numbers only (no residual tables, no secrets)
.venv/bin/python -m scripts.fleet_comms channel publish <stream-channel> \
  "handoff dual-write: file=SSOT entire=capsule. Next issues #… Merged PRs #…" \
  --sender "$SESSION_HANDOFF_AGENT" --source <harness> --kind state \
  --idempotency-key "handoff-<epic>-<date>"
```

**Cold-start companion (not a substitute for the file):** after §0 orient,
`status` + `search --query "<path-or-sha-needle>"` (and optional `handoff --query`)
so promoted SHAs surface before dispatch. Ranking is **one substring** (prefer path
tokens like `practice` or a full SHA — not multi-word sentences). Empty search =
nothing indexed for that needle; `handoff --query` with zero hits may return
`seed_invalid` — use `--locator-id` from bootstrap/search instead. Fall through to
GH issues + file handoff.

### 8a. Required live-driver inbox drain — before handoff
Immediately before writing or signalling handoff, make one final live-loop drain. Read
and apply every `unread` or `read-but-not-live-consumed` entry, then run:
```bash
.venv/bin/python -m scripts.ai_agent_bridge inbox --for "$SESSION_HANDOFF_AGENT"
.venv/bin/python -m scripts.ai_agent_bridge ack --consumed-by-live-driver <message-id> [<message-id> ...]
```
Record any action or unresolved request in the authoritative file handoff after this
drain; never claim the handoff is complete because a one-shot worker acknowledged it.
Then run the Entire dual-write steps in §8.

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
| **Grok 4.5** | Higher hallucination rate than peers → enforce tool-backed-only **harder**: never assert a word/stress/gate/count/SHA without the raw tool output quoted. 500K window — lean on plane/metrics queries, don't try to hold fleet state in context. Never take a judge seat. **FLEET-FIRST / NO SOLO (operator 2026-07-27, demotion trigger):** the operator pays for many seats on purpose and does not trust one AI; Grok is a **driver only** (dispatch → settle → cross-family CF → merge). Forbidden: multi-file implementation yourself, "quick fix" heroics, dictionary rabbit holes, ego-soloing while free codex/claude/agy/kimi lanes sit idle. Idle free lane + open work = utilization failure. |
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
