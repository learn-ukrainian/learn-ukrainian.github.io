# Task quality — DoR, DoD, blocked, residual, terminal goal

> **Scope:** Ticket- and brief-level quality for non-trivial work.
> **Nests under:** operator contract §14 / `workflow.md` pre-dispatch outcome
> adequacy (epic/phase SHA-256 packets) and
> `agents_extensions/shared/contracts/task-lifecycle-closeout.md`.
> **Does not replace:** WIP caps (`drive-epic`), CF family rules, merge-queue
> policy, or worktree layout A.

Issue hygiene and labels live in [`issue-tracking.md`](issue-tracking.md).
This doc is the required **task card** schema those issues should carry.

---

## Why

Weak tickets burn fleet time: dispatch before verify exists, close on “PR
opened”, call merge “deployed”, or leave leftovers with no owner. The pack
below makes **ready / blocked / done** explicit.

---

## Definition of Ready (DoR) — may we start / dispatch?

**DoR = Task card green ∧ Dispatch preflight green.**
Both gates must pass before substantive worker dispatch. Planning and evidence
gathering may proceed to close gaps. Operator everyday “ready” still means
**DoD (delivered)** — not this gate.

**Quality posture (binding intent at DoR; graded at CF):** research established
best practice first (`docs/best-practices/`, prior art, standards). Prefer the
**lightest elegant design** that meets the outcome and quality bar — goal- and
quality-oriented, no speculative layers “for later,” no over-engineering
(operator contract §1–2). At DoR this is the intent bar; at **cross-family CF**,
APPROVE means correct **and** not over-built relative to that posture (see
`local-code-review` / CF review skills — not satisfied by naming a CF lane).

Epic/phase kickoffs still need the full §14 outcome-adequacy packet; this DoR
is the **unit** card + preflight under that packet.

### A. Task card — may we write the work?

All must be true:

| Field | Requirement |
| --- | --- |
| **GitHub issue** | Filed issue with task description **and** acceptance criteria (use `.github/ISSUE_TEMPLATE/complex-task.md` or equivalent fields) |
| **Outcome** | One user-visible sentence (not “investigate / improve / look into”) |
| **Why / evidence** | Link, repro, metric, or failing command |
| **In scope** | Concrete paths, surfaces, modules, or APIs |
| **Non-goals** | Explicit |
| **Denominator** | What “all” means (files, modules, sample size, env) |
| **Verify** | Exact commands or held-out check named up front |
| **Acceptance criteria** | Stable IDs (`AC-01`, `AC-02`, …), each testable and mapped to denominator + Verify evidence + applicable DoD rows; semantic proof of the user outcome (green CI alone is not enough) |
| **Deps** | Blockers named or “none”; no unknown human GO mid-flight |
| **Terminal goal** | `merge` \| `deploy` \| `certify` \| `decision-only` \| `audit-only` |
| **Size** | One user-visible outcome (split if multiple); one PR unless epic child |
| **Accountable driver** | Named lane/seat that owns landing (when code) + DoD closeout |
| **Stop policy** | Failure condition · owner · disposition · unblock/transfer rule (“none expected” is not a stop policy) |
| **Residual policy** | Who owns leftovers if any; in-scope residual keeps the task unfinished unless authorized scope revision + transfer |
| **Review plan** | Anticipated author family; eligible **outside-family** reviewer; backup reviewer; explicit: advisor discussion / prompt review does **not** satisfy exact-head CF. Re-validate independence + capacity after author and review SHA are known |

For `decision-only` / `audit-only`: define the required decision or findings,
supporting evidence, disposition, and recipient. Mark irrelevant landing /
cleanup rows N/A with reasons — do not invent repo churn to “finish.”

### B. Dispatch preflight — may we run it *now*?

Tool-backed checks (**unknown ≠ green**). Each check records **command ·
timestamp · relevant output/receipt · pass criterion · failure action**.
Re-preflight **immediately before each dispatch wave and before each CF
request** — capacity and family independence are time-sensitive; a historical
green does not authorize a later start. Resources are **conjunctive**: disk
insufficiency vetoes even with quota headroom; disk alone never overrides
other failures.

| Check | Requirement |
| --- | --- |
| **Monitor / API** | Health needed for the task is green (e.g. Monitor loopback, `/api/rules` when rules bind) |
| **Task infra** | Dependencies for *this* task work (name them: sources MCP, VESUM/`sources.db`, CI, deploy target, …) — not “all infra forever” |
| **Disk** | Free disk + `.worktrees` headroom for the actual task (incl. build/test trees); **disk wins over quota** |
| **Capacity check** | Live usage + pick (`python -m scripts.fleet.usage show`, `python -m scripts.fleet.capacity_pick`) — prove numbers now |
| **Worker headroom** | When terminal goal ∈ {`merge`,`deploy`,`certify`}: ≥2 **non-orchestrator** agents with real capacity, and each required role named (implement vs independent CF — headcount ≠ independence). For `decision-only`/`audit-only`, keep applicable advisor + independent-review rules without forcing unused CF seats |
| **Fleet usable** | Target epic/stream not lease-wedged (`fleet_comms plane-status`); WIP / active dispatches OK (`/api/delegate/active`); no conflicting driver claim that blocks this start |
| **Env / secrets** | Only if required: named credentials/paths present (never print secrets) |
| **Research / routing** | Role · task-family · track · owned paths classified when dispatching (`--research-*` or deliberately generic); `ROUTING_CARD_V1` when the lane requires it |

**Trivial exempt (bounded):** may skip the full card and most preflight **only**
when **all** are true: (1) issue has label `trivial` **or** first line
`trivial:`; (2) **one-file**, non-behavioral typo/comment-only (or equivalent
single-line mechanical fix); (3) changes **no** rules, schemas, CI/security
gates, dependencies, generated artifacts, learner-facing semantics, deploy, or
certification; (4) a deterministic verify command is named. **Any doubt →
non-trivial.** Never dispatch into ENOSPC or a dead dependency the chore needs.

### Preflight command sketch (evidence, not theatre)

```bash
# Platform
curl -sfS http://127.0.0.1:8765/api/health >/dev/null
# Disk (derive .worktrees from common dir — not an arbitrary cwd)
df -h /
du -sh "$(dirname "$(git rev-parse --git-common-dir)")/.worktrees"
# Capacity + pick + worker headroom (unknown ≠ green)
.venv/bin/python -m scripts.fleet.usage show
.venv/bin/python -m scripts.fleet.capacity_pick
# Fleet usable / lease / active dispatches
.venv/bin/python -m scripts.fleet_comms plane-status
curl -sfS 'http://127.0.0.1:8765/api/delegate/active' | head -c 2000; echo
# Issue card
.venv/bin/python scripts/ci/check_issue_task_quality.py --issue N
```

Record pass/fail with timestamp + receipt for each command above.
---

## Task definition (while open)

Keep the DoR fields current. Material scope change → re-DoR + comment.
Mission-shrinking non-goals need operator/advisor approval (Fable / Astra;
Kimi may consult on non-Ukrainian design/coding only).
Re-run **dispatch preflight immediately before each dispatch wave and before
each CF request** (not only when conditions “might” have moved).

---

## Definition of Done (DoD) — may we close / claim finished?

**Operator binding (2026-09-18):** an issue/task is "**ready**" in the everyday
sense only when it is **delivered end-to-end** and git/GitHub hygiene is maintained.
That everyday "ready" is **this DoD**, not DoR. Binding copy also lives in
`operator-expectations.md` §3a (served at `/api/rules`).

A task is **not** Done when: PR opened, CF requested, CI pending, MQ
**enqueued but not merged**, "Next: …" written in a handoff, or the operator is
asked to merge. **Merge ≠ deploy ≠ certify** — match the terminal goal.
Naming a residual owner does **not** satisfy an unmet acceptance criterion;
in-scope residual keeps the task unfinished unless an authorized scope revision
and transfer resolve it.

Compose only the rows that apply (N/A needs a reason — do not skip silently):

- [ ] **Outcome verified** against denominator on the **exact merged SHA / shipped
      artifact** (and applicable env); a command run on an earlier worker head is
      insufficient; semantic proof — not CI-green alone
- [ ] Each `AC-NN` checked off with evidence link/receipt
- [ ] Verify commands green (or N/A with reason)
- [ ] Docs/templates touched by the change are updated
- [ ] If code/docs change: PR + independent **cross-family exact-head APPROVE**
      with **quality-posture receipt** (best-practice basis, root-cause treatment,
      no unnecessary architecture, no scope creep) + required CI green on that
      head + **landed** (merge verified, not merely enqueued) by the accountable
      driver — workers never merge; drivers never ask the operator to merge
- [ ] **Git hygiene:** remote branch gone, local branch gone, dispatch worktree(s)
      reaped (`merge_closeout` / `reap_worktrees.py`)
- [ ] **GitHub hygiene:** issue updated; closed when acceptance criteria are met
      (else open only with named residual + owner)
- [ ] **Terminal goal matched** — merge ≠ deploy ≠ certify.
      `decision-only`: durable approved decision + evidence + recipient.
      `audit-only`: denominator-complete findings + evidence + owned residual
- [ ] Close comment: verified outcome · denominator · merged SHA/artifact ·
      **residual** · **owner**
- [ ] Lifecycle closeout reconciled when the lane uses `task_closeout`

---

## Definition of Blocked (DoB)

“Blocked” is allowed only as **blocked-with-receipt**:

- One hold code (e.g. `dependency_blocked` \| `awaiting_operator_GO` \|
  `authoring_wip_cap` \| `review_wip_cap` \| `ci_capacity`)
- **Unblock condition** — concrete, testable
- **Owner** — who can unblock
- **Next poll / expiry** — when to re-check

Waiting on review/CI is an actionable nonterminal state — **not** “blocked”
(`task-lifecycle-closeout.md`).

---

## Residual and sizing

- Leftovers named with owner + follow-up issue/PR, or explicit “none”
- Do not copy prior-task leftovers into universal hygiene lists
- One issue ↔ one user-visible outcome; one PR ↔ one outcome

---

## Advisory check (fail-open)

Before dispatch and before close:

```bash
.venv/bin/python scripts/ci/check_issue_task_quality.py --issue N
# or score a draft body:
.venv/bin/python scripts/ci/check_issue_task_quality.py --body-file /tmp/issue.md
```

Exit `0` with `PASS` or `WARN` (missing fields listed). v1 does **not** block
merge. `--strict` fails non-zero on WARN for local gates only.

---

## Contract map (do not fork)

| Concern | Canonical |
| --- | --- |
| DoR (card + preflight) / DoD binding | `operator-expectations.md` §3b / §3a; this doc |
| Epic/phase outcome adequacy | `operator-expectations.md` §14, `workflow.md` |
| merge ≠ deploy ≠ certify; blocked-with-receipt | `task-lifecycle-closeout.md` |
| Capacity / disk / no-idle | `model-assignment.md`; `agent-activity-matrix.md` §2b |
| Ready-item + WIP holds | `drive-epic` §2 |
| Issue labels / memory | `issue-tracking.md` |

---

## Templates

- GitHub: `.github/ISSUE_TEMPLATE/complex-task.md`
- Handoffs: `docs/templates/handoff-*.md` (DoD sections point here)
- PRs: `.github/PULL_REQUEST_TEMPLATE.md` (Testing ↔ ticket Verify)
