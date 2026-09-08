# Decision: required pytest uses four verified shards

- **Date:** 2026-07-22
- **Decided by:** Sol (`gpt-5.6-sol`, bridge `advise-pytest-ci-speed-sol`, ask #4342 → #4343)
- **Issue:** #5657
- **Status:** active

## Decision

Run the hermetic required pytest selection in four deterministic shards, named
`Test (pytest) [1/4]` through `Test (pytest) [4/4]`. The shared planner collects
the existing `-k "not slow and not website"` selection and its exact ignore and
deselect list, then performs deterministic longest-processing-time assignment
from the latest main-branch duration cache. A cache miss uses equal weights
for the first run and immediately publishes measured durations for the next
run. The fresh-process cache-invalidating pair and the playground wall-clock
smoke remain serial on shard 1.

Every shard uploads its planned node IDs and JUnit result from non-hidden `ci-artifacts/` (not `.ci/`, which upload-artifact skips by default). The aggregate job
rejects missing artifacts, duplicate node IDs, an incomplete partition, or a
JUnit execution count that differs from its plan. On `push` to `main`, it also
combines the four coverage data files and enforces `--cov-fail-under=35` once.
PRs remain coverage-free.

`CI Gate` is the sole stable required check. The four display names are not
branch-protection requirements; `CI Gate` depends on the matrix job and its
artifact verifier, and explicitly rejects failed, cancelled, or skipped pytest
execution when Python changes require it. Fork PRs use the same matrix and only
the ordinary read-only GitHub token—no secret-gated job is introduced.

## Acceptance and rollback

The acceptance measurements are pytest execution p95 at or below seven minutes,
critical-path p95 at or below ten minutes, no selection or coverage regression,
and a slowest shard no more than 25% above the median shard. CI duration logs
are the source of record; any shortfall is documented rather than hidden.

Rollback is a single focused revert that restores the former one-job
`Test (pytest)` implementation and removes the shard artifact aggregation.
The separate follow-up may start pytest concurrently with lint and tune the
torch cache; neither change is part of this decision.

## Follow-up (2026-07-22): lint ∥ pytest

Sol #5657 step 6: after sharding landed, pytest matrix `needs: [changes]` only
so it starts concurrent with lint. `CI Gate` remains the sole required check and
still depends on both `lint` and `test` (plus shard-artifacts). Lint failure no
longer serializes the matrix; it still blocks merge via CI Gate.


## Follow-up: pip/torch wheel cache

Each of the four pytest shards reinstalls torch CPU wheels. Cache `~/.cache/pip`
keyed on `requirements-lock.txt` + torch 2.13.0 CPU so cache hits skip multi-GB
downloads (install still runs; download is the wall-clock cost).

## Follow-up (2026-09-08): restore LPT balance, `-n logical`, allowlist collection

#7658 (2026-09-04) replaced this decision's LPT balancing with a modulo file
split (`sed -n "${SHARD}~4p"`) and dropped the shard invocation to `-n auto`
(psutil *physical* cores). Neither was part of a superseding decision; #7816
measured the regression and this PR (`claude/ci-shard-balance-2026-09-07`)
restores the original intent with two additional, independently measured
causes fixed alongside it.

**Baseline** — run 34170483711 (`merge_group`, head `fdb69c5414`, ubuntu-latest,
4 vCPU / 2 physical cores, Python 3.12.8, pytest 9.0.3, xdist 3.8.0):

| Shard | "Run pytest" step | step-start → first test | execution window | workers |
| --- | --- | --- | --- | --- |
| 1 | 565 s | 85 s | 480 s | 2 |
| 2 | 560 s | 58 s | 502 s | 2 |
| 3 | 423 s | 73 s | 350 s | 2 |
| 4 | 542 s | 72 s | 470 s | 2 |

Attributed worker-seconds (per-worker consecutive-timestamp deltas from the
`-v` logs): 945 / 993 / 695 / 934 — the modulo split's imbalance. Seven-day
`merge_group` history: shard medians 9.6–11.3 min, p95 up to 12.8 min, run
wall-clock median 11.9 min.

**Three measured causes, restored/fixed here:**

1. **Two workers on a four-vCPU runner.** `-n auto` resolves through
   `psutil.cpu_count(logical=False)` (xdist's `pytest_xdist_auto_num_workers`)
   → physical cores, 2 of 4. Fixed: `-n logical`.
2. **Collection cost from positional file arguments.** cProfile of the
   shard-1 file list (337 files) as positional args: `isinitpath` 525,705
   calls, `_getconftestmodules` 666,791, `pathlib.relative_to` 4.5M calls, 82 s
   inside `pathlib.py`; wall 64–67 s. The same 337 files collected through
   `tests` as the single initial path plus a `pytest_ignore_collect`
   allowlist hook (`tests/conftest.py`, env var `LU_PYTEST_SHARD_FILES`):
   **8.1 s**. (`--confcutdir`, `--import-mode=importlib` do not help: 66–67 s.)
   This is a new cause beyond the original decision — collection shape, not
   test selection — fixed by the allowlist hook, never by deselecting or
   marking tests.
3. **Unbalanced modulo split.** 934/695/993/945 worker-seconds vs. this
   decision's prescribed LPT, which predicts ~892 s per shard from the same
   CI-true per-file durations. Restored via `scripts/ci/pytest_shards.py`
   `plan-files` (file-plane LPT, extending the existing planner — no second
   one) fed by a committed duration snapshot
   (`scripts/ci/pytest-file-durations.json`, refreshed by the new
   `file-durations` JUnit importer).

Not a cause (unchanged from the original decision's scope): per-test fixture
overhead. The slow tail (3% of tests holding 61% of execution) is a separate
follow-up owned by the orchestrator, not this PR.

Shard count stays 4 — this addendum does not reopen that value; a change to
5/6/8 shards is a later decision once post-PR numbers exist.
