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

All must be true (else keep planning; do not dispatch):

| Field | Requirement |
| --- | --- |
| **Outcome** | One user-visible sentence (not “investigate / improve / look into”) |
| **Why / evidence** | Link, repro, metric, or failing command |
| **In scope** | Concrete paths, surfaces, modules, or APIs |
| **Non-goals** | Explicit |
| **Denominator** | What “all” means (files, modules, sample size, env) |
| **Verify** | Exact commands or held-out check named up front |
| **Deps** | Blockers named or “none”; no unknown human GO mid-flight |
| **Terminal goal** | `merge` \| `deploy` \| `certify` \| `decision-only` \| `audit-only` |
| **Size** | One user-visible outcome (split if multiple); one PR unless epic child |

**Trivial exempt:** typo / single-line chores may skip the full card when the
issue states `trivial` (or an agreed trivial label).

Epic/phase kickoffs still need the full §14 outcome-adequacy packet; this DoR
is the **unit** card under that packet.

---

## Task definition (while open)

Keep the DoR fields current. Material scope change → re-DoR + comment.
Mission-shrinking non-goals need operator/advisor approval.

---

## Definition of Done (DoD) — may we close?

Compose only the rows that apply:

- [ ] Outcome verified against denominator (commands + evidence on the issue)
- [ ] Verify commands green (or N/A with reason)
- [ ] Docs/templates touched by the change are updated
- [ ] If code/docs change: PR + independent **cross-family exact-head APPROVE**
      + required CI green on that head + landed per merge policy
- [ ] Merge closeout when PR: remote branch gone, local branch gone, dispatch
      worktree reaped
- [ ] **Terminal goal matched** — merge ≠ deploy ≠ certify
- [ ] Close comment: verified outcome · denominator · **residual** · **owner**
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
.venv/bin/python scripts/check_issue_task_quality.py --issue N
# or score a draft body:
.venv/bin/python scripts/check_issue_task_quality.py --body-file /tmp/issue.md
```

Exit `0` with `PASS` or `WARN` (missing fields listed). v1 does **not** block
merge. `--strict` fails non-zero on WARN for local gates only.

---

## Contract map (do not fork)

| Concern | Canonical |
| --- | --- |
| Epic/phase outcome adequacy | `operator-expectations.md` §14, `workflow.md` |
| merge ≠ deploy ≠ certify; blocked-with-receipt | `task-lifecycle-closeout.md` |
| Ready-item + WIP holds | `drive-epic` §2 |
| Issue labels / memory | `issue-tracking.md` |

---

## Templates

- GitHub: `.github/ISSUE_TEMPLATE/complex-task.md`
- Handoffs: `docs/templates/handoff-*.md` (DoD sections point here)
- PRs: `.github/PULL_REQUEST_TEMPLATE.md` (Testing ↔ ticket Verify)
