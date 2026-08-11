# CI Gate and runner-slot budget

This runbook documents the CI gate and its runner-slot budget introduced by
#5818. It is
an operational guard, not a change to `ci.yml`'s job graph or `CI Gate` needs.

## CI Gate

`CI Gate` is the repository's single required check. It is the final job in
`.github/workflows/ci.yml` and succeeds only when its unconditional required
dependencies succeed: pytest planning, the `pytest-fastlane` result, all four
pytest shards, contracts, frontend, and the coverage floor. The fastlane's
changed-file selection is only an early signal: it runs directly changed test
modules first, but never selects, skips, or replaces the full-suite shard plan.
The workflow remains the authoritative job composition; this runbook
deliberately does not duplicate its YAML.

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

`CI_SLOT_CEILING = 31` in `scripts/ci/slot_inventory.py` is the only policy
source. Its baseline is the measured 29 PR runner slots, including the
parallel pytest fastlane and four pytest shards; two slots are deliberate
headroom.
The same command runs inside the existing always-on `actionlint` PR workflow,
so a workflow edit cannot silently bypass the budget and the guard adds no
runner job of its own.

To raise the ceiling, submit a focused one-line PR changing
`CI_SLOT_CEILING`, with the inventory's measured before/after output and the
reason the added concurrency is safe. Do not raise it as a side effect of an
unrelated workflow change.

Mutation proof: temporarily add a dummy PR job in a local scratch copy of the
workflow directory whose static matrix raises the total above 31, then run the
inventory. The unit test models the measured 29-slot baseline plus a three-way
dummy job and verifies the nonzero exit. Do not commit a dummy job.

## Local Linux filesystem parity

On macOS, platform-sensitive filesystem tests are unverified until they pass
in a local Linux container or GitHub Actions Linux. Run the focused parity
probe before push:

```bash
make test-linux-fs
```

It mounts the repository read-only in `python:3.12-bookworm` and runs existing
tests for real worktree containment, primary-checkout guards, executable hook
modes, and deploy-script symlink handling. The explicit list is in
`scripts/ci/linux_fs_parity.sh`; add a file only when it covers Linux-relevant
filesystem semantics, so this stays a quick parity signal rather than another
full-suite path.

## Changed-test fastlane

`scripts/ci/changed_tests.py --base <base-sha-or-ref>` produces a deterministic,
newline-delimited file plan from changed conventional test modules under
`tests/`. An empty plan is successful and intentional for docs-only or
implementation-only changes. It currently does not infer tests from changed
implementation files; the unconditional shards remain responsible for that
coverage.

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
