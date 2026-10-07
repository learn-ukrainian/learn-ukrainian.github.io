# Dispatch push validation

The harness prepends a per-worktree `git` wrapper to worker PATH. Auto-finalize
calls the same validator directly. The wrapper intercepts push before Git,
so `git push --no-verify` still validates. Ordinary Git hooks remain available;
the validator explicitly invokes pre-commit's pre-push stage over the committed
base/head range. This is a supported-command boundary, like the dispatch pytest
cap, not a sandbox against deliberate executable or environment replacement.

Supported worker forms are `git push [-u] [--no-verify] origin HEAD`, the current
branch in place of HEAD, and omitted origin/current-branch arguments. Quiet,
porcelain, force-with-lease and `-C` naming the assigned worktree are also supported. Ambiguous global options,
other destinations, multiple refs, tags, deletions and main pushes fail closed.
Workers must use this wrapper; absolute Git executables, aliases, transport
changes or PATH replacement are unsupported. Auto-finalize does not rely on PATH.

The smallest blocking set is:

- Existing pre-commit pre-push checks over `merge-base(origin/main, HEAD)..HEAD`.
- The versioned `scripts/ci/push_invariants.json` authority for the existing
  `repo_wide` modules and individual test IDs. Its existing marker/completeness
  tests still check the authority against actual pytest marks.
- Changed Python test files, independent of imports. Whole files absorb duplicate
  individual node IDs. Deleted tests are not invoked.

The worktree must match the outgoing HEAD and be clean. Validation binds its
receipt to HEAD, the base and registry digest. Both paths recheck the receipt
and send a literal commit ID, so moving a branch cannot swap the tested commit.
The outgoing merge range starts at the freshly observed remote branch when it
exists; already-published merges are not reclassified. Force-with-lease is pinned
to that observed remote SHA. The existing runtime push scanner is retained, and
may independently refuse `--no-verify`; it cannot bypass validation.
Ambient pre-commit `SKIP` and pytest options cannot weaken the checks. Full CI
and merge-group CI remain unchanged and authoritative for other failures.

One shared Git-common-directory lock admits one gate across linked dispatch
worktrees. Admission is fail-fast: contention produces `validation_incomplete`
with `admission_busy`, records admission latency, and returns to the driver.
Blocking execution has a ten-minute deadline; checks run serially with no xdist
fan-out, allowing the runner and one nested collector. Timeout kills the child
process group. Red produces `validation_failed` and failing pytest IDs; any
unknown or exhausted attempt produces `validation_incomplete`. No retry occurs.
Auto-finalize preserves its commit on either validation refusal.

Local, untracked receipts live under the worktree Git admin `push-gate/`:
`receipt.json`, append-only `attempts.jsonl`, `pre-push.log`, and `pytest.log`.
They contain range/head, registry digest, selected tests, failing node IDs,
execution/admission seconds, typed status, and merge evidence. They are diagnostic
evidence, not independent review or CI approval, and must not be committed.

Every attempt also records importer closure in `shadow`: mode, status,
`closure_tests`, `selected_tests`, `unresolved_dependencies`, and `full_fallback`.
It reuses the component dependency scanner. Unresolved edges project the full
test inventory but execute none of it. Shadow errors/timeouts record unavailable
and never block; its independent maximum is thirty seconds. This remains shadow
until driver-owned independent fault injection proves adequacy.

Merge origin/main only on a merge-tree conflict against freshly fetched main,
driver disposition supported by base/head/combined-tree evidence, or driver order.
A broken base is not repaired by merging it; merge-tree errors stay unknown.
Before pushing a merge, write `push-gate/merge-reasons.json` under the Git admin:

```json
{
  "<merge SHA>": {"reason": "driver_order", "evidence": "<driver disposition receipt>"}
}
```

`driver_disposition` additionally requires `base`, `head`, and `combined_tree`.
`conflict` requires `base`: the gate freshly fetches main, verifies it is the
merge's second parent, and requires merge-tree exit 1 against the first parent.
Missing, stale or unknown evidence refuses the push. Every new head needs renewed
independent review and CI. Merge-group CI proves semantic combinations.

The driver owns critical cross-family review, CI, merge, cleanup, deployment,
and the two-week before/after first-attempt CI/flake-adjusted and delivery-latency
measurement for #10033. Local gate receipts provide refusals, exhaustion,
admission and execution measurements; they cannot establish avoided rework.
