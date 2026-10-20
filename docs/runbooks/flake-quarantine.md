# Flake quarantine admission

Issue #10608 uses the existing `tests/flake_quarantine.yaml` registry and
`pytest-rerunfailures`. Admission never skips a test or changes its assertions.
An eligible first failure gets one rerun. A second failure and pytest timeouts
fail the job. Scheduled runs and `LU_FLAKE_DISABLE_RERUN=1` disable reruns.
Recovered failures remain visible in the terminal, JUnit `flake.reruns`
property, Actions summary and existing nightly flake ledger.

## Evidence required for an entry

- `node_id`: the exact pytest node, including class and parameter ID when present.
  File, class and function patterns are refused.
- `observed_run_ids`: at least two distinct GitHub Actions run IDs. Each must
  be completed CI on unmodified `main` in this repository, with its head SHA
  still in `main` history. The checker refuses PR, merge-group and other workflow evidence.
  Downloaded `pytest-junit-shard-*` artifacts must report the exact node failing,
  erroring, or passing after a recorded first failure in each run. A failing
  workflow without the node's failure is insufficient.
- `fix_issue` and `owner`: an open repair issue and an accountable repair owner.
  A PR number cannot replace the repair issue.
- `equivalent_coverage`: a mapping from other exact pytest nodes to explanations
  of the behavior each preserves. Each node must pass without reruns in both
  baseline runs. Designated approvers judge whether these assertions provide
  equivalent behavior coverage, including their continued execution in CI.
- `admitted_on`, `expires_on`, `renewals`: the existing date limits apply.
  Initial expiry is at most 30 days after admission. At most one renewal is
  allowed, with `renewed_on` within the original 30 days and expiry at most
  30 days after renewal. After expiry plus seven grace days, reruns stop.
- `admission_approval`: the numeric ID of a designated approval record comment
  on the repair issue. A trusted repository publisher records the operator's
  approval or the agreeing designated advisors' approval, with provenance and
  the coverage judgment, before the entry is admitted. Ordinary discussion or
  independent implementation review cannot replace this designated decision.

The approval comment must contain this marker on its own line, replacing
`DIGEST` with `admission_digest(entry)` from
`scripts.common.flake_quarantine`:

```text
<!-- flake-quarantine-admission:DIGEST:APPROVE -->
```

The digest is SHA-256 of sorted JSON for all entry fields except
`admission_approval`, with date values represented as ISO strings. The comment
ID is excluded so the publisher can compute the digest before posting it.
The checker verifies the comment's repair-issue identity, repository affiliation
and exact digest. The trusted publisher attests designated approval provenance;
the checker does not infer model identity or coverage adequacy from prose.
Changing any admission field, including renewal dates, needs a new bound approval.

## Verify before admission

Set `PROJECT_PYTHON` to the interpreter prescribed by the task. Run this command
from its dispatch worktree:

```bash
"$PROJECT_PYTHON" -m scripts.common.flake_quarantine --base-ref origin/main
```

Use the PR or merge-group base SHA when replaying that event. The CI Checks job
runs this command against that trusted base with read-only GitHub permissions.
Missing, expired, malformed or unavailable evidence refuses admission. Repair
missing evidence before requesting another admission check.

Every run lints the complete registry offline. New entries and changed entries,
including renewals, additionally require online admission checks. Unchanged
entries need no downloads because Actions artifacts can expire before the
quarantine does. Removing an entry requires no new admission. Pytest collection
uses offline lint and exact-node selection, with no GitHub dependency.

The registry starts empty. This change admits no existing flake. The existing
nightly expiry announcements, seven-day grace and escalation ledger remain in
effect. See [the CI speed program](../epics/ci-speed-program.md) for D2 behavior.
