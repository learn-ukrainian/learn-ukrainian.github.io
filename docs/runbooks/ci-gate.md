# CI Gate

`.github/workflows/ci.yml` is one small workflow (ci-v3, 2026-09-30). `CI Gate`
is the only required GitHub check. Every `pull_request`, `merge_group`,
`schedule` (03:30 UTC on `main`) and `workflow_dispatch` run executes the same
jobs and the full non-slow pytest suite. There are no path tiers, test areas,
import-graph selection or labels: a change cannot pick which tests it runs.
Slow tests (`@pytest.mark.slow`) run in `pytest-slow-nightly.yml`.

| Job | What it does |
| --- | --- |
| Reuse check | `merge_group` only. Looks for a green full run of the identical tree (below). |
| Queue commit metadata scan | `merge_group` only, reuse or not. TruffleHog over the queue commit's message, author and committer (below). |
| Secret scan | Event-aware TruffleHog range, OPSEC public-identifier lint, internal-ID check. Skipped only on a recorded merge-queue reuse. |
| Checks | `scripts/ci/checks.sh`: every lint and content-contract gate; runs all, fails if any failed. Skipped only on a recorded merge-queue reuse. |
| Frontend | Builds and tests the site when the diff touches the frontend denominator; otherwise exits green after the scope step. Skipped only on a recorded merge-queue reuse. |
| pytest (1..N) | The full `not atlas_release and not slow` suite, split over N static shards. Skipped only on a recorded merge-queue reuse. |
| pytest report | Whole-run checks over every shard; records the tested tree, commit, PR and run. |
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
| needs_artifact collected set == `registry/artifacts/needs-artifact-expected.txt` | Needs artifact audit (separate `--collect-only`) | pytest report, from each shard's collected list (tests/conftest.py writes it before `-m` deselects) |
| needs_artifact skip set == the same expected set | Needs artifact audit (separate run) | pytest report, from the shards' JUnit |
| Every test file ran | none (planner trust) | pytest report: shard file lists must partition `git ls-files tests` |
| Full-history checkout where tests read old commits | pytest, Fast checks, Contracts | pytest shard 1 (the history shard), Checks, Frontend, Secret scan; pytest shards 2..N are shallow |
| Queue commit metadata (message, author, committer) scanned for secrets | Secret scan, every queue run | Secret scan on a full queue run; Queue commit metadata scan on every queue run |
| TypeSafe triage (advisory) | Fast checks, `continue-on-error` | `ci-advisory.yml` (not required) |
| Atlas POC richness, vocabulary coverage (advisory) | Contracts, `continue-on-error` | `ci-advisory.yml` (not required) |
| Slow tests, quarantine run, flake ledger, failure issue | `pytest-slow-nightly.yml` | unchanged |

The needs_artifact audit makes two independent comparisons with the expected
list. The collected set comes from collection, before `-m` deselects anything:
each shard sets `LU_PYTEST_NEEDS_ARTIFACT_COLLECTED` and `tests/conftest.py`
writes every marked test it collected (xdist worker gw0 writes; all workers
collect the same items). The outer pytest removes the variable from its
environment and hands the path to its workers through xdist's `workerinput`,
so a test that starts a child pytest cannot overwrite the shard's list with
the child's. Run 36658788394 lost 77 ids that way, in the three shards holding
such tests; `test_nested_pytest_leaves_the_collected_list_intact` covers it.
The skip set comes from the JUnit reports. In CI no
artifact store is present, so every marked test must run in the tier and skip
with the `needs_artifact:` message. A marked test deselected as `slow`, skipped
for another reason, or passing is in the collected set but not the skip set,
and fails the report.

Executed outcomes were compared test by test with the old workflow on the same
base: the old run 36648511336 (merge-queue run of `252ea0fa64`) against the new
run 36658788394. 36,322 test ids ran in both. Every one of them had the same
outcome, except the fixed-port dashboard smoke described under pytest shards.
Both runs skipped all 368 expected needs_artifact tests. The 192 ids found
only in the old run and the 124 found only in the new run all belong to CI
test files this change deleted or rewrote.

## CI Gate

CI Gate needs every other job and checks each result:

- Reuse check and Queue commit metadata scan: `skipped` outside the merge
  queue, `success` inside it (the metadata scan also on a reuse).
- Secret scan, Checks, Frontend, pytest and pytest report: `success`, except in
  a merge-queue run whose Reuse check reported `reuse=true` with a run id; then
  all five must be `skipped`, and the gate logs the reused run for each.

`cancelled`, a missing result or any other value fails the gate. The gate runs
under `always()` because GitHub treats a skipped required check as passing.
`tests/test_ci_pr_triggers.py` executes the gate script against every case.

## Merge queue: reuse of an identical tree

A `merge_group` commit whose tree equals the tree a `pull_request` run of the
queued PR already tested in full holds the same code; running the same jobs
again cannot learn anything. `scripts/ci/reuse_green_run.py`:

1. computes `git rev-parse <merge_group.head_sha>^{tree}`;
2. reads the queued PR number from the queue ref, then the PR's head SHA, and
   the pytest shard matrix from the queue commit's `ci.yml`;
3. lists successful `pull_request` runs of `ci.yml` for that head SHA;
4. reuses the first run that proves all of:
   - the run: `pull_request`, `ci.yml`, completed `success`, for the PR's
     current head, in its first and only attempt;
   - its `ci-tested-tree` record (written by `pytest report` only after every
     shard passed and the report's checks held): `tier: full`, the queued PR's
     number, this run's id and attempt 1, more than zero tests, a commit SHA;
   - that commit, read from GitHub's API rather than the record: a merge whose
     parents include the PR head (the pull_request merge commit) and whose tree
     is the queue commit's tree; the record names the same tree;
   - the run's attempt-1 jobs: exactly Secret scan, Checks, Frontend,
     `pytest (1..N)`, pytest report and CI Gate, each once and `success`; the
     two queue-only jobs `skipped`; nothing else.

Anything else runs every job: a different tree (main moved, or several PRs in
one group), no record (older runs, expired artifacts), another PR's record, a
zero-test or non-full record, a re-run, a job that is missing, duplicated,
unexpected or not `success`, or any lookup error. The decision, the reused run
and every reused job's id are in the Reuse check's job summary; CI Gate's log
names the reused run for each skipped job. A reused queue run is the Reuse
check, the Queue commit metadata scan and CI Gate.

Reusing Secret scan and Checks is sound for the file contents they read: the
scanned diff and the checked tree. With an identical tree, every line the queue
commit adds over `main` was either added by the PR's commits, which the PR run
scanned, or already on `main`. The diff-scoped checks see the same diff,
because an identical tree in practice means `main` has not moved.

The queue commit's own metadata is new: the queue writes PR-derived text into
its message, and TruffleHog scans each commit's message, author and committer
as well as its diff. The Queue commit metadata scan therefore runs on every
queue run. `scripts/ci/metadata_commit.py` writes a commit with the queue
commit's author, committer and message, its first parent as the only parent
and that parent's tree, and TruffleHog scans `parent..that commit`: an empty
diff, so the scan reads the metadata alone.

Because the pull_request run already executes every job, reuse applies
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
  runner's cores, so one long file no longer pins a shard. The old workflow
  used `--dist=loadfile`, so tests of one file never overlapped. Tests that
  share a fixed resource must now serialize themselves: the two fixed-port
  smokes in `tests/test_work_dashboard_private_integration.py` take a file
  lock in the run's shared temp root. Without the lock, one of them skipped
  with "ports busy" in every new-workflow run.
- A stale durations file only costs balance, never coverage. Refresh it from a
  full run's JUnit when shard times drift:

  ```bash
  gh run download <run-id> --pattern 'pytest-junit-shard-*' --dir /tmp/junit
  .venv/bin/python -m scripts.ci.split_tests durations /tmp/junit/*/*.xml > scripts/ci/pytest-file-durations.json
  ```

### History shard

Seven test files are listed in `scripts/ci/history-tests.txt`. Five read old
commits: `git show`/`git cat-file` of an old SHA, a recorded historical
commit, a frozen base commit, and `origin/main` ancestry. Two run a
`--dry-run` `delegate.py dispatch --worktree`, which fetches `main` from
GitHub. On a shallow checkout that fetch downloads all of main's history, 65-77
s per test instead of 0.3 s. `split_tests.py` pins the listed files to shard 1
and balances the other files around them. Shard 1 is the only shard checked out
with full history (`fetch-depth: 0`). Shards 2..N check out only the tested
commit (`fetch-depth: 1`) and run pytest with `GIT_ALLOW_PROTOCOL=file`. A
listed file that is no longer tracked fails the split.

The list is measured, not guessed. Run 36654595606 had every shard shallow
with network git blocked in the pytest step. It was compared test by test with
the full-history run 36650655215. Only these seven files changed outcome (28
tests, passed to failed). The one other change is a `test_ci_split` workflow
assertion that failed on the experiment's own `GIT_ALLOW_PROTOCOL` edit. None of them skipped:
each failed loudly, with git exit 128 or a blocked https transport. Without the
block, the network fetch in the two delegate tests pulled main's history into
their shard and hid two of the five history files. A new test that needs
history or fetches from GitHub therefore fails on a shallow shard; add its file
to the list.

To change the shard count, edit the static `matrix.shard` list (it must stay
`1..N`). `scripts/ci/slot_inventory.py --check` (actionlint workflow) counts
every PR-path job against the 58-slot ceiling (GitHub Team: 60 concurrent
jobs, two reserved).

## Shard setup

Per shard: checkout (shallow; full history on the history shard), Python
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
