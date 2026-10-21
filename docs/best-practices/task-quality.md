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

On issue open or edit, `.github/workflows/issue-task-quality.yml` refetches the
current issue and reconciles one `issue-task-quality:v1` bot comment. DevOps
owns it. It fails only for non-trivial malformed DoD structure, conflicting
ancestry, or a new issue with no native parent at observation time. Each event
walks native ancestry once, at most eight parent reads, without a full-tree
audit or retries. Full orphan and body-evidence classification belongs to the
dispatch check. It is not a required check for code PRs. Parent-link changes
do not trigger this workflow; dispatch always checks live parentage again.
The comment records the UTC membership observation time and never reproduces
issue body text.

The checker reports DoR, DoD structure and membership separately. DoD structure
uses `task_lifecycle.parse_issue_acceptance_criteria`: stable-ID checkboxes may
be unchecked or checked at admission. Missing structure is
`dod_structure_absent`; malformed or duplicate IDs are
`dod_structure_malformed`, with the canonical parser diagnostic. Completion
still requires the delivery evidence below. The trivial exemption covers card
fields and missing DoD structure, never live membership. Malformed DoD on a
trivial card remains visible in the DoD section, comment and report, but does
not refuse admission. Body-only CLI modes report
membership `unchecked` and cannot establish membership proof.

Acceptance items that explicitly require evidence after merge, post-merge,
once merged, or after landing must name `owner: <lane>` and a valid calendar
date as `due: YYYY-MM-DD` on the same line. The recognized lanes are
`claude-infra`, `codex-devops`, `codex-atlas`, `grok-monitor`,
`gemini-open-model-data`, and `claude-cto`. The date is the deadline to collect
and review the evidence. Missing or invalid fields produce
`post_merge_unowned` WARN, which blocks implementation dispatch unless a reason
is recorded. Generic mentions of runs, windows, days, or receipts alone do
not trigger this rule. Fenced code blocks and quoted examples are excluded.

```markdown
- [ ] AC-03: After merge, review five CI receipts; owner: codex-devops; due: 2026-11-20
```

The live checker follows at most eight repository-qualified parent links to a
registered active root and calls `resolve_live_ancestry`. Active roots retain
only their documented membership exemption. Canonical fresh unique body
evidence is accepted as `pending_native_link`. Overflow containers remain
ordinary issues. Conflicting roots, multiple owners, cycles and cross-repository
parents refuse admission without an override. Read failures, depth exhaustion,
timeouts and stale or incomplete audits are unknown, never proof of membership.
After a live read confirms that the target itself has no native parent, dispatch
tries the shared `batch_state/issue_stream_audit.json` cache. The existing audit
validator must certify completeness, shape and freshness within 3600 seconds.
The report must match the target repository and current stream registry, and
the exact target number must have unique body membership for the claimed root.
An invalid, conflicting, missing or unreadable cache cannot admit the target.
It falls back to a live audit within the same membership budget. A failed
fallback records both its typed refusal and the cache rejection reason. Native
parent traversal does not read the cache or run the audit.

The daily issue-quality report and successful bounded live checks publish the
cache through `write_membership_cache`. It validates the repository, current
registry, complete traversal, listing denominator and conflict-free effective
membership before writing. A sibling temporary file is flushed and synced,
then renamed over the shared cache atomically. Failed validation or a failed
write leaves the previous cache intact. The payload retains the audit's original
`generated_at`, `membership_complete`, index and open-issue numbers. It adds
`schema_version: 1` and `root_results`, which lists each registered root's
effective native and body members. Readers validate versioned per-root results
against the index; existing unversioned audit reports retain their canonical
validation. No new process or timer is required. Daily publication retries
reuse the saved report bytes and do not renew the membership timestamp.

The Monitor serves this same file at `/api/issues/streams`, so every
publication is a complete hygiene report. The writer appends the closed-epic and
milestone warnings that `run_audit` adds, from the same shared helper. If that
lookup fails, nothing is written. `root_results` is private like the
membership index: both the route and the Work projection strip every key in
`PRIVATE_CACHE_KEYS`. A checker's verdict is final before publication, so a
deadline or write failure during publication keeps the verdict and records
`cache_write_error` (`membership_audit_cache_write_timeout` or
`membership_audit_cache_write_failed`).

A parentless issue resolves only when the audit records exact unique body
membership, even if its own title or body has no parent claim. A valid audit
that observed the open target but found no stream returns
`membership_unregistered_parentless`, without repeating the live audit. Its
message gives the registration step: link the issue as a native sub-issue of
one registered root or its overflow container. If native linking is at capacity,
add `- [ ] #N` to exactly one registered root's body and refresh the audit.
A target absent from the snapshot still needs a live audit. A fresh cache
does not register a new issue by itself.

Issue fetching and membership observation each have a 60-second budget,
including cache validation and the entire live audit. Together they leave 15
seconds for overhead inside dispatch's 135-second checker timeout. Timeout codes
identify `membership_timeout_target_fetch`,
`membership_timeout_cached_audit_validation`, `membership_timeout_live_audit_open_issues`,
or `membership_timeout_live_audit_root_N_of_M_issue_K`, naming the root's position
and the issue being read, including descendants. Native parent-read timeouts
retain `membership_timeout`. A membership timeout preserves the fetched card's
DoR and DoD findings. A target-fetch timeout adds its typed code to
`checker_error`; other fetch failures report `checker_error`. Membership cannot
be established when the target fetch fails.

Implementation dispatch checks both workspace-write and danger modes; read-only
triage stays exempt. Non-trivial malformed DoD and conflicting ancestry cannot
be overridden.
Absent DoD, missing parent, unavailable registry and unknown membership refuse
by default, with the existing recorded `--allow-dor-warn REASON` exception.
Cursor Auto refuses any override. Registered fleet repositories without a
membership registry report `membership_not_applicable` in admission, while DoR
and DoD remain required. They need no permanent override.

The separate daily `issue_quality_report` service and timer summarize all
repositories from `fleet_repos.load_fleet_repos()`. One audit per registered
repository supplies membership. An independent GraphQL open-issue count checks
the listing denominator; a limit hit or count mismatch marks coverage incomplete.
Unreachable data is unknown, never zero defects. Private repositories expose
only counts, with membership explicitly incomplete under `membership_unknown`
and `membership_registry_absent`. Payloads use `issue-quality-report.v1`, persist
under ignored `batch_state/reports/`, and retry the same bytes with a UTC-date
Fleet Comms idempotency key. Publication failure exits non-zero.
Root issues count toward DoR and DoD totals like other issues; their exemption
applies only to membership. A date other than today can only retry a saved
payload; the report refuses to label a current snapshot with another date.
Installation and live delivery proof belong to DevOps; this source change
installs nothing.
The private issue workflow and hramatka event wiring remain DevOps-owned work.

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
| **Fleet usable** | Target epic/stream not lease-wedged (`.venv/bin/python -m scripts.fleet_comms plane-status`); WIP / active dispatches OK (`/api/delegate/active`); no conflicting driver claim that blocks this start |
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
Mission-shrinking non-goals need operator/advisor approval (Opus 5.5 and Sol 6.1 agreeing; when one of them
authored the proposal, the other's approval completes it; any other author needs both; Kimi: web, UI and backend coding only).
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

After merge, run `.venv/bin/python -m scripts.orchestration.postmerge_criteria
--pr N --apply`. For the PR's closing links and explicit `Closes #N` references,
the command reopens closed issues with unchecked acceptance criteria and posts
one comment per outstanding item set with each owner and deadline. Missing or
invalid assignments go to `claude-cto` through Fleet Comms, idempotently per
issue and item set. Dry-run omits `--apply`; outstanding criteria return exit 1.
The owning lane checks due items in its existing reconciliation cycle, records
evidence, and escalates overdue items. Naming an owner never satisfies an item.
This command does not close issues or audit historical issues.

Follow-up for the separate `merge_closeout.py` owner: call
`postmerge_criteria.run_postmerge_criteria(pr_number, apply=apply)` after
confirming MERGED and before reporting successful closeout; propagate a false
`ok` as unfinished closeout. The integration is not installed by #11213.

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

## Advisory issue check and strict dispatch gate

Before dispatch and before close:

```bash
.venv/bin/python scripts/ci/check_issue_task_quality.py --issue N
# or score a draft body:
.venv/bin/python scripts/ci/check_issue_task_quality.py --body-file /tmp/issue.md
```

Without `--strict`, the advisory CLI exits `0` with `PASS` or `WARN` (missing
fields listed), including when GitHub/API input cannot be read. It does **not**
block issue creation or merge. Implementation dispatch uses `--strict`: WARN,
GitHub/API lookup failure, or checker failure refuses dispatch by default.
The recorded `--allow-dor-warn <reason>` exception covers absent DoD or missing
and unknown membership. Malformed DoD and conflicting ancestry remain
non-overrideable. PR references are skipped after API resolution; a brief
without an issue reference is not gated. The detailed admission rules are above.

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
