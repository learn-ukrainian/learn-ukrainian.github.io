# CI Gate and runner-slot budget

This runbook documents the CI gate and its runner-slot budget introduced by
#5818. It is
an operational guard, not a change to `ci.yml`'s job graph or `CI Gate` needs.

## CI Gate

`CI Gate` is the repository's single required check. It is the final job in
`.github/workflows/ci.yml` and succeeds only when its unconditional required
dependencies succeed: pytest planning and all four pytest shards, contracts,
frontend, and the coverage floor. The workflow remains the authoritative job
composition; this runbook deliberately does not duplicate its YAML.

The contracts job's BIO preparation validation is load-bearing. In particular,
an active BIO hold must continue to fail closed (`PREPARATION_HOLD_ACTIVE`),
and the check refuses a change that would make an active hold pass
vacuously. Do not remove, path-filter, or move that validation to an advisory
workflow.

## Runner-slot budget

Run the inventory locally from the repository root:

```bash
/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -m scripts.ci.slot_inventory --check
```

The script parses every `.github/workflows/*.yml` that runs on `pull_request`
or `merge_group`. It counts each top-level job and expands static matrix
dimensions, exclusions, and additions. It fails closed on an unsupported
dynamic matrix. The documented pytest-shard runtime matrix is the exception:
`PYTEST_SHARD_CEILING` is pinned to four and asserts that the static `ci.yml`
matrix does not exceed that topology.

`CI_SLOT_CEILING = 30` in `scripts/ci/slot_inventory.py` is the only policy
source. Its baseline is the measured 28 PR runner slots on #5818's main
baseline, including the four pytest shards; two slots are deliberate headroom.
The same command runs inside the existing always-on `actionlint` PR workflow,
so a workflow edit cannot silently bypass the budget and the guard adds no
runner job of its own.

To raise the ceiling, submit a focused one-line PR changing
`CI_SLOT_CEILING`, with the inventory's measured before/after output and the
reason the added concurrency is safe. Do not raise it as a side effect of an
unrelated workflow change.

Mutation proof: temporarily add a dummy PR job in a local scratch copy of the
workflow directory whose static matrix raises the total above 30, then run the
inventory. The unit test models the measured 28-slot baseline plus a three-way
dummy job and verifies the nonzero exit. Do not commit a dummy job.

## Quarantine convention (documentation only)

If a future CI-capacity exception must be recorded, describe it in the PR or
issue using this convention; this runbook creates no ledger and does not adopt
the #5812 implementation list:

```yaml
reason: why the exception is necessary
owner: accountable maintainer or team
exit_condition: measurable condition, expiry date, or tracking issue
```

Every entry needs all three fields. The `exit_condition` must provide a
concrete removal path, not an open-ended intention. For incident context, see
the CI-gate autopsy at `docs/bug-autopsies/2026-07-25-invisible-ci-gate.md`.
