# Pre-push gate (#10033)

`.githooks/pre-push` runs `.githooks/pre_push_gate.py` on the exact outgoing commit before any push
leaves a checkout. Worker `git push` and the auto-finalize push (`scripts/delegate.py`) both go through
it. Install and repair the hook chain with `scripts/install_git_hooks.sh`.

## What it checks

For each pushed branch (deletes and tags are skipped), with `HEAD` equal to the pushed commit and no
tracked changes:

1. `pre-commit run --hook-stage pre-push --from-ref <base> --to-ref <head>` over the outgoing range.
   `<base>` is the remote tip when it is an ancestor, else the merge-base with `origin/main`.
2. The invariant registry: `KNOWN_REPO_WIDE_MODULES` and `KNOWN_REPO_WIDE_FUNCTIONS` in
   `tests/test_repo_wide_marker_invariant.py`, read by AST and deduplicated (a function id is dropped
   when its whole file is selected). Its version is a digest of the gate version and the ids.
3. Test files the range adds or changes (`tests/**/test_*.py`).

Stages 2 and 3 run as one pytest process. Importer-closure selection
(`scripts/ci/pre_push_shadow.py`) runs beside them in shadow: recorded, never blocking.

## Outcomes

| Outcome | Exit | Meaning |
| --- | --- | --- |
| green | 0 | Push proceeds; a receipt is written. |
| `pre_commit_failed`, `tests_failed` | 1 | Push refused; failing hook names or pytest node ids are listed. |
| `tree_mismatch`, `dirty_tree`, `range_unresolved`, `invalid_ref_updates` | 1 | The exact commit cannot be validated as pushed. |
| `validation_incomplete` | 75 | Not validated and not green: `admission_timeout`, `timeout`, `registry_unavailable`, pytest without a verdict. The branch is preserved; return to the driver. Never retry blindly. |

The last stderr line before the bypass hint is machine-readable: `{"pre_push_gate": {...}}`.

## Bounds

One admitted gate per repository at a time (lock under the Git common dir), admission wait 300 s, run
budget 600 s, one test process (ceiling 2). `LU_PRE_PUSH_GATE_ADMISSION_WAIT_S` and
`LU_PRE_PUSH_GATE_RUN_BUDGET_S` can only shorten these.

## Receipts

`<git-common-dir>/lu-pre-push-gate/receipts/<head>.json` lets a retry of the same commit skip the run. It is
bound to the commit, tree, base, registry version, selected ids and gate version, expires after one hour, and
is ignored when any of them differ or the tree is dirty.

## Measurement (AC-05)

Every run appends a row to `<git-common-dir>/lu-pre-push-gate/measurements.jsonl`: outcome, reason, failing
ids, admission wait, duration, registry version and the shadow selection. Join with first-attempt CI outcome
per PR head for the before/after report.

## Merge-main rule

Merge `origin/main` into a worker branch only when `git merge-tree` against a freshly fetched main SHA reports
a conflict, when the driver disposes on base/head/combined-tree evidence that the branch is incompatible with
the base, or on driver order. A merge-tree error is unknown, not a conflict. Every new head needs renewed
approval and CI; merge-group CI stays the authority for semantic combinations.

## Bypass

`git push --no-verify` is the explicit operator bypass; the rescue path in `scripts/delegate.py` uses it
deliberately. Agent sessions must not.
