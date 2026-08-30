---
name: drive-epic
description: Model-agnostic orchestrator playbook for driving ONE epic/track lane end-to-end over the fleet-comms message plane. Invoke this when you are launched as an epic/track driver (Grok, Sonnet-5, Gemini/AGY, Kimi, Claude, or Cursor) via a start-<model>-driver.sh --epic launch and told to "drive this epic". Teaches the METHOD — topology → route → dispatch → settle → cross-family review → merge → handoff — and defers all live roster/routing DATA to /api/rules and model_catalog.yaml. Not for main-orchestrator cold-start (that has its own hook) and not for writing a single module (use $track-completion).
effort: xhigh
---

# Drive an epic lane

You were launched to **drive one epic/track lane** (`SESSION_EPIC` is set). You are
**NOT** the main orchestrator. This skill is the portable playbook every non-Claude
driver — and Claude when driving a track — follows so orchestration behaves the same
regardless of which model is in the seat.

**Golden rule of this skill: it teaches the *method*, never the *roster*.** Who is in
which lane, which model fits which task, and the current width (CodexBar pace/reserve +
disk headroom, not a fixed cap) are **live data** that change; always read them fresh from
the served rules and catalog, never from memory:

- `GET http://127.0.0.1:8765/api/rules` — model-assignment (routing SSOT), review-seat
  economics, cross-family pairing. Served first; supports `If-None-Match`.
- `scripts/config/model_catalog.yaml` — machine-enforced quality floors + ordered peer
  tiers per task-risk.
- `docs/best-practices/agent-activity-matrix.md` §2/§2b — roster + no-idle capacity routing.

**Driver role (not a clerk).** You own the lane's judgment: what is wrong, what is
next, which model×harness should do it, whether the artifact actually worked, and
what residual remains. Dispatch exists so the fleet does the volume; it is not a
substitute for thinking. Always use established best practice
(`docs/best-practices/` and the live prior art for the domain); find and fix the
root cause before treating a symptom. You decide in-scope calls. You are not a
designated advisor (Fable/Sol) and not the CF of record for work you drove — you
*do* read the review and the diff before you merge. Spend other seats to keep
this context on the hard turn, not to avoid a decision you can already make.
Unused paid quota is waste (§2c); manufactured work is a defect. Judgment is not
implementation — seat no-solo rules still bind.

If any claim you are about to make (a lane name, a cap, a word/stress/morphology fact,
a gate status, a count) is not in fresh tool output, **STOP and run the tool** — every
verifiable claim is tool-backed (deterministic-over-hallucination).

**Work-board orientation surface:** `GET http://127.0.0.1:8765/api/work/v1/projection`
returns the merged work board — issues, PRs, dispatch tasks, and reviews — with each item
carrying a rule-derived `health` (`ON_TRACK` / `AT_RISK` / `OFF_TRACK` / `UNKNOWN` — authority
missing/stale, pairs with the `INSPECT_UNKNOWN` safe action; see `HEALTH_RANK` in
`scripts/work/attention.py`), an `attention_rank`, and a `safe_next_action`. Query it at orient
and again when picking the next unblocked action (§2); it is a queue INPUT alongside your
stream/GH/issue sources, never a replacement for them.

**Stream next-queue:** `GET http://127.0.0.1:8765/api/work/v1/next?stream=<your-stream>`
returns a compact, stream-scoped actionable pick list (default `limit` 7). Consult it at orient
and next-action time alongside the projection — also a queue INPUT, never a replacement. Cold
(absent) cache → `503` `building` + `retry_after_s` (does not trigger a build); unknown
`stream` → `400` with `valid_streams`.

---

## The loop (run it every cycle)

### 0. Orient

```bash
curl -sS --max-time 2 "http://127.0.0.1:8765/api/orient?lean=true" || true
curl -sS --max-time 2 "http://127.0.0.1:8765/api/work/v1/projection" || true  # best-effort: local server, degraded/absent sources are normal
curl -sS --max-time 2 "http://127.0.0.1:8765/api/work/v1/next?stream=<your-stream>" || true  # stream-scoped pick list (#6880)
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
stale in-context snapshot. For per-lane budget health before dispatch:
`.venv/bin/python -m scripts.fleet.capacity_pick` then
`scripts/delegate.py dispatch --check-budget` (or `LU_DISPATCH_CHECK_BUDGET=1`)
(+ `/api/state/routing-budget` for subscription lanes).

### 2. Pick the next unblocked action

Source of next work: your epic's stream tail / handoff, open GH issues for the epic, the
build/review queue, the Work API projection's ranked attention list (§0), and
`GET /api/work/v1/next?stream=<your-stream>` — cross-check against them before committing to
an action. **Step 0 of any dispatch:** `gh pr list --state all
--search "<issue-nr>"` by issue reference (an open issue ≠ unfixed; a sibling PR may already
carry it). If nothing genuinely fits a free lane, log it and leave it idle — never
manufacture busywork (quality > utilization).

### 2-epic. Epic issue ownership cycle (binding — operator 2026-08-28)

You are an **epic orchestrator**, not a clerk waiting on one PR. Every cycle must advance
the epic's open issue set:

1. **Inventory** — open GitHub issues for this epic/stream (plus Work API `/next` +
   grok-bot QA issues per §2b). Quote the count.
2. **Disposition each item** — for every open issue, exactly one of:
   - **in_flight** (named PR/task id + head),
   - **dispatch now** (ROUTING_CARD + `capacity_pick` / `/api/state/routing-budget` +
     `--check-budget`),
   - **named hold** with one §2c code (`dependency_blocked | authoring_wip_cap |
     review_wip_cap | ci_capacity | worktree_wip_cap | disk_capacity |
     integration_wip_cap | human_decision | no_ready_work`).
3. **Silence is a defect** — an open epic issue with no disposition is a driver failure.
4. **Closeout** — after merge: close the issue (or prove residual), then follow §7a order
   (P0 reaper first, then branch deletion). Merge alone is not done.

**Anti-passive (all seats, Cursor especially):** while CF or CI runs on unit N, you
**must** either dispatch the next ready epic child or emit a §2c disposition code in the
same turn. Ending a turn with only "waiting on review/CI" and no fill/disposition is
forbidden. Overnight/session gaps do not excuse an unfinished CLEAN/MERGEABLE PR —
re-read checks and finish merge/hygiene on the next live turn.

### 2a. NO FABRICATED DONE (binding all epic drivers)

- Never invent acceptance thresholds the operator, issue, or epic goal did not set.
- Never declare a goal done while measured residual remains in the same mandate unless
  tools prove it impossible or the operator accepted it on the issue.
- Never end with "when you want" or an "optional next" for in-scope residual — dispatch it.
- Never relabel unfinished work as an intentional skip without issue text or tool proof.
- Before "done" or handback, quote the tool residual count; `residual > 0` requires a
  next dispatch in the same session.

### 2b. Grok-bot QA findings — queue input, not a fleet seat

Grok Bot (`app/cursor`) is an **external QA observer** — it reads CI/site signals and files
labeled GitHub issues; drivers consume those issues through the normal loop above like any
other open issue. It is **never** a dispatch target: no `--agent grok-bot`, no `ask-grok-bot`,
no fleet-comms seat. If Grok Bot ever authors a PR, same-family Grok must not CF it — route to
an outside-family reviewer per §6. Full contract: `docs/runbooks/grok-bot-qa-observer.md`.

### 2c. No idle lanes — subscription min-max (binding, all driver seats)

Idle paid lanes are direct financial loss (operator 2026-08-17). This generalizes the
Grok-seat fleet-first *utilization* rule to **every** driver seat.

**Definitions.** *Free lane* — healthy, budget-eligible seat with no live assignment.
*Ready item* — queued work that is valuable, unblocked, and has an integration path.
*Compatible / independent* — the item fits the free lane and does not collide with
in-flight units (paths, review identity, or a hard dependency). *Settle event* — any
dispatch/review/CI terminal or decision point. *Grace period* — the short fill window
after a settle event before a hold is allowed. *Epic done* — operator goal met with
tool-backed residual 0, or operator-accepted residual on the issue.

**Precedence (strict):** correctness/quality → safety/resource bounds →
dependency/critical-path → utilization. Later items never override earlier ones.

1. **Waits are dispatch windows.** After any dispatch or review ask, **before** holding,
   fill every free lane with a compatible ready item (unblocked work, banked follow-ups,
   or prep the next program child whose dependency allows it). Idle free lane + ready
   item = utilization failure.
2. **Authorized idle is not a utilization failure.** A settle-hold must name one code:
   `dependency_blocked | authoring_wip_cap | review_wip_cap | ci_capacity |
   worktree_wip_cap | disk_capacity | integration_wip_cap | human_decision |
   no_ready_work`. Silence is not a disposition.
3. **Pipeline with a depth limit.** While CF/CI runs on unit N, author N+1 only up to
   the WIP/resource cap. Unit N **regains priority** the moment review feedback returns.
   Never serialize implement → review → delta with idle gaps.
4. **Ready-work forecast.** An unfinished epic needs a current ready-work forecast. An
   empty ready queue requires an explicit disposition, not silence. File banked
   follow-ups as GitHub issues when identified. Empty stream `/next` is a driver defect
   unless the epic is done or a disposition applies.
5. **Anti-gaming.** No placeholder agents, artificial task splitting, premature PRs, or
   speculative work without an integration path. §2 still binds: never manufacture
   busywork (quality > utilization). Disk wins every conflict (#M-14 — `df` + `du` of
   `.worktrees` before fan-out; reap first).

Mechanical reminder + disposition telemetry (#6976/#6998). At every
dispatch/review settle, evaluate eligible ready items and first-class admission
WIP limits (authoring / review / CI / worktrees / disk / integration) plus
queue readiness. The reminder fires only when something is eligible; then
dispatch or pass a structured code. Unknown codes are rejected. Do not add a
raw idle-time threshold. Guardrail-authorized idle is not a failure.
`driver_breadth_report --enforce` fails the breadth floor (unless NOTE-waived)
and MISSING/DISHONEST idle dispositions — never opportunity-seconds.

```bash
.venv/bin/python -m scripts.orchestration.dispatch_settle task --task-id <id> \
  --idle-snapshot-json <snap.json> [--dispatched | --disposition <code>]
.venv/bin/python -m scripts.fleet.idle_settle evaluate \
  --snapshot-json <snap.json> --kind dispatch --task-id <id> \
  [--dispatched | --disposition <code>]
.venv/bin/python -m scripts.fleet.idle_settle report
.venv/bin/python -m scripts.fleet.idle_settle admission --snapshot-json <snap.json>
.venv/bin/python -m scripts.fleet.driver_breadth_report --initiator grok --since-hours 24 --enforce
```

### 3. Route by model × harness fit

Decide the lane from `/api/rules` + `model_catalog.yaml`, **never** from the provider
name. Respect the live caps (in-flight ceilings), the language-lane restriction
(UK authoring / linguistic / content review route only to the sanctioned language lanes
per the served rules), folk carve-outs (cross-family only), and the judge-seat rules.
On limit: note the substitution and reroute per the fallback table — never block on one lane.

**Live capacity (binding every implement / CF settle):** before picking a seat, read
fresh tool output from **both**:

```bash
curl -sS --max-time 3 "http://127.0.0.1:8765/api/state/routing-budget"
.venv/bin/python -m scripts.fleet.capacity_pick
```

Prefer cooler / higher-headroom seats from that data. Do **not** habit-route to a hot or
in-flight-saturated lane when a cooler eligible seat exists. CodexBar is an **input to
the API**, not a separate driver app workflow — if both surfaces are empty/stale, probe
and record that in the ROUTING_CARD (`NOTE: routing_budget_empty`), then use `/api/rules`
fallback tables. Never invent burn % from memory.

### 3-routing. Mandatory ROUTING_CARD_V1 + breadth (operator GO 2026-08-06)

**Binding full text:** `agents_extensions/shared/rules/fleet-driver-routing.md` (served at
`/api/rules` after model-assignment).

Before **every** implement `delegate.py dispatch`:

1. Emit a **ROUTING_CARD_V1** (handoff / issue / `batch_state/` receipt) with:
   `tier` (authority|practical|heap) · `model_x_harness` · `why_this_tier` ·
   `advisor_packet` (required if tier=heap) · `owned_paths` · `acceptance_cmd` ·
   ≥2 `alternatives_considered` · `parallel_free_seats` · quoted
   `routing_budget_primary` + `capacity_pick_order` (tool evidence).
2. **No card = no dispatch.** Skipping the card is a process defect; do not launch the
   worker and "write the card later."
3. **Default bounded work:** Fable or Sol **brief** → heap/practical **worker(s)** —
   not a Sonnet/Terra fixation solo. Heap without advisor packet is a process defect.
4. **Fable path:** native `claude-fable-5` or Cursor pin to Fable; do not spend Fable on
   lockfiles / pointer / smoke jobs.
5. After ≥3 implement dispatches this session, require ≥2 agents **and** ≥2 tiers **or** a
   written `NOTE: fleet_breadth` with tool-backed blockers.
6. Before handoff, run and attach:
   ```bash
   .venv/bin/python -m scripts.fleet.driver_breadth_report --initiator "$SESSION_HANDOFF_AGENT" --since-hours 24
   # optional hard check:
   .venv/bin/python -m scripts.fleet.driver_breadth_report --initiator grok --since-hours 24 --enforce
   ```

Fixation on one practical seat while free lanes sit idle = utilization failure
(§2c — all driver seats, not Grok-only).

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

**Capacity-first (binding — operator 2026-08-12 / #4707):** Before every implement
dispatch, run `capacity_pick` and pass `--check-budget` (or export
`LU_DISPATCH_CHECK_BUDGET=1` in the launcher):

```bash
.venv/bin/python -m scripts.fleet.capacity_pick
.venv/bin/python scripts/delegate.py dispatch --check-budget --agent <lane> --worktree ...
```

Refuse habit-routing to hot / near_cap / CodexBar-deficit lanes when cooler seats
are listed. `--check-budget` hard-subs via `dispatch_fallbacks` when mapped
(e.g. `codex → cursor`); otherwise exits non-zero unless `--force-agent` + NOTE.

Then dispatch with a numbered brief
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
This wait is a §2c fill window, not an idle period: fill free lanes before holding.
Terminal vocab (match `scripts/delegate.py`): **`done` = SUCCESS** (NOT "completed");
other terminal/attention states: `failed | timeout | rate_limited | cancelled |
crashed | dry_run` (dry_run is terminal, not success) + `needs_finalize | no_deliverable`. Emit on any
status NOT in `{spawning, running, ""}`. The task file is truth; `/api/delegate/active`
can omit live tasks. **Before declaring a dispatch dead:** `gh pr list --state open`
first, then check the worktree for finished-but-unpushed work. **After terminal status,**
run `.venv/bin/python -m scripts.fleet.post_task_reap --task-id <id>` (dry-run by default;
pass `--apply` to reap the bound dispatch worktree). `post_task_reap` delegates removal to
the P0 reaper; do not substitute a direct Git removal path.

### 5a. Required live-driver inbox drain — after settle

Once the settle-loop reaches its decision point, drain again before choosing the next
action. Read and apply every `unread` or `read-but-not-live-consumed` entry, then run:
```bash
.venv/bin/python -m scripts.ai_agent_bridge inbox --for "$SESSION_HANDOFF_AGENT"
.venv/bin/python -m scripts.ai_agent_bridge ack --consumed-by-live-driver <message-id> [<message-id> ...]
```

### 6. Cross-family review gate (load-bearing — discussion ≠ review)

A review of record is **independent and cross-family** (outside the author's model
family; never self-review, never same-family).

- **Execution and comms layers:** CF, design, and plan use toolful seats (`delegate.py` or native harnesses); ACP is toolless intercomm only, and caveman lite is style (never persisted review text).

**Shielded formal CF is RETIRED (operator 2026-08-07).** Do **not** run
`review-pr` / sealed `lu-review-*` / `shielded-reviews` clones — the CLI fails
closed. Use lightweight direct review:

```bash
printf '%s\n' "Cross-family review of PR #<N> at head <SHA>: VERDICT + findings." | \
  .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-<lane> - \
    --task-id review-<N> --type review
# Post verdict on the PR, then merge when CI is green.
```

This command line is unchanged, but the transport underneath it is not ACP
(operator 2026-08-23, #7155): `--type review` / `--review` / `--pr` / `--branch`
route to a headless native CLI with tools (`delegate.py dispatch --agent <lane>
--worktree`, `gh`/pytest available), never the tool-less `--deny-all --no-fs
--no-terminal` chat transport. ACP stays for ordinary, non-review `ask-*`.

Pick the reviewer family from the served reviewer-seat rule; the writer's family
is never eligible. Read the review CONTENT (not just pass/fail), apply deltas,
re-probe gate-driving data yourself.

### 7. Merge discipline

PRs only — never commit or merge to `main` directly. **Arm auto-merge the moment the
review gate passes AND blocking CI is green:**
```bash
gh pr merge --auto --squash
```
Do **not** pass `--delete-branch` here while this repo uses a merge queue — deleting the
head mid-queue can close the PR without landing. Delete the remote branch only after
`gh pr view` shows `MERGED`, as part of §7a cleanup. Never arm on a **draft** and never
merge ahead of the review verdict. Blocking CI red → never `--admin`-bypass. A
track/infra driver **self-merges its own lane's PR** after the cross-family gate + green
CI (lane model — there is no promoting orchestrator). Flag another lane's PR with
`needs=merge` rather than merging it.
Skill- or docs-only landings classify as merge_group `docs_skills` (#7018):
the four pytest shards and coverage combine are no-op **success**, not skipped.

**Merge-queue kick is same-hour work (#7042).** A **kick** is `merge_group` CI Gate
going red and GitHub dequeuing the PR — it lands back on the branch looking CLEAN,
with no visible failure unless you go look. CI Gate now comments the source PR with
the run URL and per-job `RESULTS` on a kick; that comment is the trigger, not a
courtesy. On seeing it: read the failed jobs from the run, fix or rebase, re-run
exact-head CF review if the head moved, then re-queue — same hour, never left
overnight. Do not stand up a bot or recovery workflow for this; it is driver work
like any other red CI.

### 7-rollout. Local / production proof (when the epic requires it)

Do **not** make every epic driver a standing release owner. Gate rollout by charter:

| Kind | Driver owns? |
| --- | --- |
| **Local / service proof** after a change (restart Monitor API, smoke `/api/…`, UI check) | **Yes** — part of verifying the artifact |
| **Host pull / service restart** in epic/issue scope | **Only on present-tense operator trigger** — issue text sets scope, not authorization |
| **Production / Pages / public cutover** | **Only on present-tense operator GO** — listing it in the epic establishes scope, not a green light |
| **HA / Patroni / new VPS / fenced cutover** | **Escalate** — operator/advisor GO; drive the checklist, do not solo mutate |

Missing local proof on a user-visible API/UI change is incomplete closeout. Issue/PR wording
never substitutes for operator-triggered deploys or present-tense GO (operator contract
item 10). Claiming prod HA without that GO is out of scope.

### 7a. Post-merge cleanup is mandatory (binding — operator 2026-08-07)

**A squash-merge is not done until cleanup proves free of that PR's residue.** Chat
promises do not bind; this section does. Leaving dispatch worktrees or tmp residue
after merge is a process defect (ENOSPC / disk full is the known failure mode).
**Never pass `--delete-branch` to `gh pr merge` when the repo uses a merge queue** —
deleting the head ref mid-queue can close the PR without landing (known failure mode).
After `MERGED`, follow the numbered order below: reaper first, then branch deletion.

**Order after `gh pr view <N>` shows `MERGED`:**

1. **Confirm** merge SHA.
2. **P0 reaper first** — after all processes have left the target worktree, run:
   ```bash
   .venv/bin/python -m scripts.orchestration.reap_worktrees --apply --merged \
     --worktree .worktrees/dispatch/<agent>/<task>
   ```
   This closed loop removes only a clean worktree whose PR is `MERGED` at its exact head.
3. **Manual fallback only** — if the reaper cannot run, follow
   [`worktree-cleanup.md`](../../../../docs/runbooks/worktree-cleanup.md) for the
   kill switch, rescue restore, and allowlisted dual paths before using
   `git worktree remove`.
4. **Branches** — after the worktree is reaped, **verify** the local branch is gone
   (`--merged` reaper already deletes it). Delete manually only if it remains (fallback).
   Confirm the remote is gone; then run `git fetch --prune` and `git worktree prune`.
5. **Prove** — `df -h /` and `git worktree list` show no zombie for that PR.

**Do not** treat merge alone as closeout. **Do not** run sealed formal CF.

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
Then run the Entire file-handoff steps in §8.

---

## Fleet-comms state — dual-aware, cutover is closed

The message plane's `authority` cutover is **done**: mode `authority` is the production
default (operator GO 2026-08-01, closed with evidence on
[#6159](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6159)).
Fleet-comms is now durable authority for messages/jobs; legacy broker/channel file
stores are read-only migration/projection inputs, not a live write target.

- **Cold-start first action:**
  `.venv/bin/python -m scripts.fleet_comms cold-start-board` — probes fleet/plane/stream
  state so you orient from live data, never memory.
- **Check plane state:** `.venv/bin/python -m scripts.fleet_comms plane-status` and
  `.venv/bin/python -m agents_extensions.shared.session_streams dual-write-status`.
  Implemented modes are `off | shadow | dual_write | authority` — do not hard-code a
  mode in prose; always query it fresh.
- **File handoff still matters:** fleet-comms is durable authority for messages/jobs,
  but you still write file continuity where the epic uses one (`.claude/<epic>-epic/
  *DRIVER-HANDOFF.md` — gitignored local state — or `docs/session-state/` for infra); see
  the file-handoff steps in §8. Successor-claim diagnostics: `session_streams
  handoff-status` / `handoff-claim` (#5530).
- **Sealed formal CF is retired** — CF is the direct `ask-<lane>` + PR-post flow in §6,
  not `review-pr` / sealed `lu-review-*`.
- **ACP provider transport:** ACP is toolless intercomm only (state transfer / ordinary asks/discuss); CF, design, and plan use toolful seats (`delegate.py` or native harnesses), and caveman lite is style.
- **Never** flip the plane, enable retention apply, or invent a competing comms design
  from this skill — those remain the infra lane's gated actions, even post-cutover.

---

## Per-model capability delta

Same playbook; each seat adjusts on the axes the fleet has measured. This is the ONLY
model-specific section — everything above is identical across seats. **§2c (no idle
lanes / subscription min-max) is not a per-model delta** — it binds every driver seat.
The Grok row's remaining seat-specific rule is no-solo *implementation* (driver-only),
not the utilization half.

| Seat | Delta |
| --- | --- |
| **Grok 4.6** | Tool-backed claims still bind on this seat (operator 2026-07-27): never assert a word/stress/gate/count/SHA without the raw tool output quoted — that is policy, not a 4.6 quality ranking. 500K window — lean on plane/metrics queries, don't try to hold fleet state in context. Never take a judge seat. **FLEET-FIRST / NO SOLO (operator 2026-07-27, demotion trigger):** the operator pays for many seats on purpose and does not trust one AI; Grok is a **driver only** (dispatch → settle → cross-family CF → merge). Forbidden: multi-file implementation yourself, "quick fix" heroics, dictionary rabbit holes, ego-soloing. **No-solo means you do not implement; it does not mean you stop thinking.** Utilization (idle free lane + open work) is §2c and binds every driver seat — not a Grok-only delta. |
| **Sonnet-5** | You are authority-capable (near-Opus judgment, 1M window) → make the judgment call and escalate **less**; still escalate the genuinely architecture/process class (below). CF reviews you route must go to a **non-Anthropic** family (you are Anthropic-family — avoid self/same-family review). |
| **Gemini / AGY (gemini-3.7-flash-high)** | Harness/infra scope. MCP-leading tool use + 1M window + low cost = ideal infra driver. **Do not claim curriculum content lanes.** Route UK-language work to the sanctioned language lanes, not to yourself. |
| **Kimi K3** | Frontier coder/reviewer + cross-family escalation authority (independent of Anthropic & OpenAI). `max-effort-only` makes a continuous loop costly — drive when assigned, else stay a reviewer/escalation seat. |
| **Claude (when driving a track)** | Prefer **Sonnet-5** for routine track driving; reserve Opus for the hardest judgment + the CF review of record so Opus quota stays free. If the seat is **Opus 5**, apply the **Claude Opus 5** row below (do not restate its mitigations here). |
| **Claude Opus 5 (when in the driver seat)** | **Documented damage modes** (Anthropic *Migrating to Claude Opus 5* + *Prompting Claude Opus 5* — encode, do not invent): scope expansion, over-delegation, verification loops when told to verify, premature done claims, verbose handoffs. **Routing:** routine driving → **Sonnet-5**; Opus 5 for judgment moments / reviews of record, **not** long solo drives (same preference as Claude row; seat adjustment, not a roster). **Scope (quote):** "Deliver what was asked, at the scope intended. Make routine judgment calls yourself, and check in only when different readings of the request would lead to materially different work. If the request seems mistaken or a better approach exists, say so in a sentence and continue with the task as asked rather than quietly narrowing, widening, or transforming it. Finish the whole task, and stop short of actions that are clearly beyond what was asked." **Delegation hard cap (Opus 5 over-delegates — inverse of lean-in for earlier Opus):** "Delegate to a subagent only for large tasks that are genuinely independent and parallelizable… Do not delegate work you can finish yourself in a handful of tool calls, and do not use subagents to verify or double-check your own work. If one subagent can complete the task, use one rather than several, and keep spawn counts low." Prefer `scripts/delegate.py` fleet dispatch over intra-session subagent spawn for real work. Filling free fleet lanes per §2c is required and is not intra-session subagent spawn. **Verification scaffolding — DELETE:** Opus 5 "verifies its own work without being told to"; remove / do not add explicit verify / double-check / "use a subagent to verify" instructions — they "cause over-verification". Self-correction already strong; avoid "re-verify before responding". **Handoffs / verbosity (effort ≠ length):** default responses and written deliverables run longer; lowering effort "reduces thinking volume without reliably shortening the visible response." Calibrate: keep handoffs brief, lead with outcome; "Match the length of written documents to what the task needs… do not pad with filler sections, redundant summaries, or boilerplate." **Corrections without rumination:** "Only correct an earlier statement when the error would change the user's code, conclusions, or decisions. State corrections plainly and briefly, then continue the task." **Thinking-config guards:** thinking is on by default; **never** `thinking: disabled` in the driver seat (prefer lower effort for cost). `thinking: {type: "disabled"}` + effort `xhigh`/`max` is a **rejected request** (400). Drive at `high`, bump `xhigh` for the hard judgment turn, then drop back. |
| **Codex / GPT-5.6 Terra** | Named alternate only for harness / infra (`epic:4707`) and the independent DevOps stream (`epic:5703`). The launcher injects the HydrationCapsuleV1 cold-start board and binds at most one exact fresh CLI rollover; stop on any SessionStart setup error. Codex has no Monitor-equivalent watcher, so use bounded foreground waits and escalate hard judgment to Sol. |
| **Cursor (Auto)** | Launched via `./start-cursor-driver.sh --epic <epic>` (#6956). Keep Auto; pin `grok-4.6` / `composer-2.5` only when family independence must be frozen. Driver-of-record requires attested `resolved_model` (unattested Auto cannot be driver-of-record). **Concurrency 1:** this driver session **is** the Cursor lane — do **not** `delegate.py dispatch --agent cursor` from inside it (deadlock / quota contention). Runtime note: stream leases serialize one **driver** per epic stream (`already has live session`); `delegate.py` does **not** fail-closed against a live Cursor driver lease — capacity is a non-blocking hint only. GUI Cursor IDE remains human supervision, not a second driver protocol. **Anti-passive (Cursor):** this seat has repeatedly failed by stopping at "CF/CI pending" overnight. Binding: every turn that does not merge/hygiene a CLEAN gate must §2-epic-dispose the next issue or name a §2c code; a CLEAN/MERGEABLE PR with CF APPROVE must be merge-queued the same turn (no `--delete-branch` until MERGED). Session end without that closeout is a driver defect. |

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
