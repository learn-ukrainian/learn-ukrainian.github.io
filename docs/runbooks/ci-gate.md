# CI Gate

`.github/workflows/ci.yml` is one small workflow (ci-v3, 2026-09-30). `CI Gate`
is the only required GitHub check. Every `pull_request`, `merge_group`,
`schedule` (03:30 UTC on `main`) and `workflow_dispatch` run executes the same
jobs and the full non-slow pytest suite. There are no path tiers, test areas,
import-graph selection or labels: a change cannot pick which tests it runs.
Slow tests (`@pytest.mark.slow`) run in `pytest-slow-nightly.yml`.

| Job | What it does |
| --- | --- |
| Reuse check | `merge_group` only. Looks for a green full pytest run of the identical tree (below). |
| Secret scan | Event-aware TruffleHog range, OPSEC public-identifier lint, internal-ID check. |
| Checks | `scripts/ci/checks.sh`: every lint and content-contract gate; runs all, fails if any failed. |
| Frontend | Builds and tests the site when the diff touches the frontend denominator; otherwise exits green after the scope step. |
| pytest (1..N) | The full `not atlas_release and not slow` suite, split over N static shards. Skipped only on a recorded merge-queue reuse. |
| pytest report | Whole-run checks over every shard; records the tested tree. |
| CI Gate | `if: always()`; fails on any job result other than the expected one. |

`ci-advisory.yml` (pull_request only, never required) carries the advisory
checks: TypeSafe triage (#8232), Atlas POC richness (#3930) and the diff-scoped
Atlas vocabulary coverage report.

## Gate inventory

Every gate of the previous `ci.yml` and where it lives now. Only the machinery
that chose *which* tests or checks a change ran is gone.

| Gate | Before | Now |
| --- | --- | --- |
| TruffleHog, event-aware range (`secret_scan_scope.py`) | Secret scan | Secret scan (unchanged) |
| OPSEC public identifiers (`lint_opsec_leaks.py`) | Secret scan | Secret scan (unchanged) |
| Internal IDs (`check_no_internal_ids.py`) | Secret scan | Secret scan (unchanged) |
| Read-only token (`permissions: contents: read`) | workflow | workflow; `reuse` adds `actions`/`pull-requests: read` |
| Credential-free checkout (`persist-credentials: false`) | every checkout | every checkout (tested) |
| SHA-pinned actions | every `uses:` | every `uses:` (tested; actionlint + zizmor) |
| Ruff lint (`ruff check scripts/ tests/ agents_extensions/ dashboards/`) | Fast checks, not docs-only | checks.sh, every run. `ruff format --check` stays off (~2,050 files differ). |
| Strict v2 plan validation | Fast checks | checks.sh (same PR path scoping) |
| Arc landing drift (`build_arc_landing a1 --check`) | Fast checks | checks.sh |
| Word Atlas sense-lint ratchet | Contracts | checks.sh |
| Lesson-schema drift | Contracts | checks.sh |
| MDX source/forward parity, generation drift | Contracts | checks.sh |
| Teacher cloze content | Contracts | checks.sh |
| Locked module not published | Contracts | checks.sh |
| Atlas manifest freshness and enrichment | Contracts | checks.sh (the manifest load itself is in `python-ci-env`) |
| Static practice assets | Contracts | checks.sh |
| Dossier word counts | Contracts | checks.sh |
| BIO preparation capsules and holds | Contracts (inline Python) | checks.sh → `scripts/ci/bio_preparation_gate.py` |
| Frontend build, generated-artifact drift (before test:unit re-runs hydrate), unit and built-output tests | Frontend, when the denominator matched | Frontend (same denominator, same order) |
| Frontend change denominator incl. backend hydrate inputs | Changes (`classify_changes`) | Frontend scope step (`frontend_change_scope.py`); completeness kept by `tests/test_frontend_denominator_invariant.py` |
| Full non-slow pytest, strict markers, `--timeout=120` | pytest shards (full/selected/docs/content tiers) | pytest shards, full suite on every event |
| Postgres tests must not skip (`pg_skip_guard.py`) | per shard | per shard |
| needs_artifact skip set == `registry/artifacts/needs-artifact-expected.txt` | Needs artifact audit (separate collection + run) | pytest report, from the shards' JUnit (no second collection) |
| Every test file ran | none (planner trust) | pytest report: shard file lists must partition `git ls-files tests` |
| Full-history checkout where tests read old commits | pytest, Fast checks, Contracts | pytest, Checks, Frontend, Secret scan |
| TypeSafe triage (advisory) | Fast checks, `continue-on-error` | `ci-advisory.yml` (not required) |
| Atlas POC richness, vocabulary coverage (advisory) | Contracts, `continue-on-error` | `ci-advisory.yml` (not required) |
| Slow tests, quarantine run, flake ledger, failure issue | `pytest-slow-nightly.yml` | unchanged |

The needs_artifact audit used to also compare the *collected* marked set with
the expected list. In CI no artifact store is present, so every marked test in
the suite either skips with the `needs_artifact:` message (and is compared) or
fails its shard; the skip-set comparison covers both halves.

## CI Gate

CI Gate needs every other job and checks each result:

- Secret scan, Checks, Frontend: `success`.
- Reuse check: `skipped` outside the merge queue, `success` inside it.
- pytest and pytest report: `success`, except in a merge-queue run whose Reuse
  check reported `reuse=true` with a run id; then both must be `skipped`.

`cancelled`, a missing result or any other value fails the gate. The gate runs
under `always()` because GitHub treats a skipped required check as passing.
`tests/test_ci_pr_triggers.py` executes the gate script against every case.

## Merge queue: reuse of an identical tree

A `merge_group` commit whose tree equals the tree a `pull_request` run of the
queued PR already tested in full holds the same code; running the suite again
cannot learn anything. `scripts/ci/reuse_green_run.py`:

1. computes `git rev-parse <merge_group.head_sha>^{tree}`;
2. reads the queued PR number from the queue ref, then the PR's head SHA;
3. lists successful `pull_request` runs of `ci.yml` for that head SHA;
4. downloads each run's `ci-tested-tree` artifact, written by `pytest report`
   only after every shard passed and the partition held (`tier: full`);
5. reuses the first run whose record has `tier: full` and the same tree.

Anything else runs the full suite: a different tree (main moved, or several PRs
in one group), no record (older runs, expired artifacts), a record that is not
the full tier, or any lookup error. The decision and the reused run id are in
the Reuse check's job summary and in CI Gate's log. The rest of the jobs
(secret scan, checks, frontend) always run in the queue.

Because the pull_request run already executes the full suite, reuse applies
whenever `main` has not moved between the PR's last green run and its queue
entry.

## pytest shards

- `scripts/ci/split_tests.py split` assigns the tracked `tests/**/test_*.py`
  files to N shards, longest first onto the least-loaded shard, using
  `scripts/ci/pytest-file-durations.json`. A file with no recorded time gets
  the median. Every shard computes the same assignment; the shard number and
  count come from `matrix.shard` and `strategy.job-total`.
- The shard collects through one `tests` path; the `LU_PYTEST_SHARD_FILES`
  allowlist hook in `tests/conftest.py` keeps collection to the shard's files.
- Within a shard, `-n logical --dist=worksteal` spreads single tests over the
  runner's cores, so one long file no longer pins a shard.
- A stale durations file only costs balance, never coverage. Refresh it from a
  full run's JUnit when shard times drift:

  ```bash
  gh run download <run-id> --pattern 'pytest-junit-shard-*' --dir /tmp/junit
  .venv/bin/python -m scripts.ci.split_tests durations /tmp/junit/*/*.xml > scripts/ci/pytest-file-durations.json
  ```

To change the shard count, edit the static `matrix.shard` list (it must stay
`1..N`). `scripts/ci/slot_inventory.py --check` (actionlint workflow) counts
every PR-path job against the 58-slot ceiling (GitHub Team: 60 concurrent
jobs, two reserved).

## Shard setup

Per shard: checkout (full history: some tests read old commits), Python
3.12.8, then `scripts/ci/test_env.sh start` runs `npm ci` and
`scripts/ci/start_postgres.sh` (bubblewrap, PostgreSQL 16 cluster, DSN
verification) in the background while `python-ci-env` installs the locked
environment from main's exact-key uv cache; `test_env.sh wait` fails the job if
either background task failed. A container image was not adopted: the checkout
cannot be inside an image, and pulling a prebuilt environment of this size
costs about what the cache restore does (see the measurements in the ci-v3 PR).

## Cloud advisory runner dependency parity (#6977 slice A)

`scripts/ci/cursor_cloud_full_pytest.sh` (the offline-verifiable Cursor cloud
pytest prototype; see `docs/design/2026-09-06-cloud-agent-pytest-advisory.md`)
mirrors the `python-ci-env` install: same lockfile exclude set
(`torch`/`torchvision`/`open_clip_torch`/`stanza`), `uv pip` when available,
`packages/v4-runtime --no-build-isolation` + `build_assets.py`, and an
unconditional hard-fail manifest hydrate. It also requires
`LEARN_UKRAINIAN_CP_PG_DSN` whenever control-plane tests are selected, and
detects (never sudo-installs) the native deps `scripts/ci/start_postgres.sh`
provisions (`bubblewrap`, `libpq`). It plans node-ID shards with
`scripts/ci/pytest_shards.py` (`plan` / `run` / `verify-artifacts`), which
GitHub Actions no longer uses. **When the CI dependency install changes,
update the runner script to match** — a drifted runner is a false-green risk.
Runner ↔ CI parity is covered offline by
`tests/ci/test_cursor_cloud_pytest_verify.py`.
