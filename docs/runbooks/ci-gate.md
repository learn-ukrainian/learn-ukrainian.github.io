# CI Gate

`.github/workflows/ci.yml` emits the required `CI Gate` context in two tiers.
PR events run admission checks: file-content secret scanning, the large-file
guard, attribution, lint and content contracts, dependency-audit scoping,
`pytest --collect-only` and Frontend. They run no pytest shards; the gate summary
states plainly that full pytest was not run (operator decision, 2026-10-29).
The parallel required `pr-affected` job executes literal changed existing
`tests/**/test_*.py` files, every path in `scripts/ci/pr-affected-guards.txt`, and
the tests that directly import, load, read or run a changed non-test file.
The same job also runs `pytest tests -m 'repo_wide and not atlas_release and not slow and not site_toolchain'`
in a separate required step.
This selects marked tests only, including marked functions in otherwise
unmarked files. Its traversal includes `tests/build/`, which pytest normally
excludes. It uses the same candidate identity and checkout-integrity checks.
The invariant step runs even if changed tests defer or fail, unless the run
is cancelled. Changed-file duration estimates never defer invariants.
It verifies the checked-out candidate against `GITHUB_SHA` and the event's PR
merge ref. The candidate must have two Git parents and its second parent must
match the event's PR head. Its first parent supplies the actual tested base for
the diff. Event base metadata can be stale, and fetched target refs can advance;
neither replaces that immutable parent. No fetched-target, event-base ancestry,
`GITHUB_BASE_REF` or untracked-file admission check is required. Tracked source
changes still fail the checkout-integrity check.
The diff uses NUL-delimited Git paths, rename destinations and tracked regular
files. Deleted files are reported.
Unsafe paths, missing guards and symlinks fail closed. Tests for changed code come
from the direct edges of the static scan in `scripts/ci/components.py`
(`scan_imports`): imports, literal loads, file reads and Python subprocess targets.
Only direct importers are selected; the transitive closure spans most of the suite,
which the merge group runs. A deleted file has no edges in the candidate, so the
surviving tests that depended on it come from the same scan of the base tree.
The component inventory chooses no tests.

CI does not run on PR title and body edits; an edit would restart the whole
suite on an unchanged head. The `Scan PR publication fields` job in
`pr-publication-scan.yml` runs on every PR event, including edits, and on queue
candidates. It and the CI Secret scan job read title, body, branch and complete
commit messages from the event and current PR metadata using the existing OPSEC
rules. Queue scans
read every member of the first-parent squash chain and each member's current
PR metadata and source commits. On `merge_group`, CI Gate repeats that scan as
its last step, so an edit made while the queue run was testing still blocks. A missing field, incomplete checkout, unsupported
event or unreadable range fails closed. Submitted values are never diagnostics
or workflow environment inputs. The advisory PR-body guard also scans direct
push branch names and complete commit ranges. A new topic branch uses its
unique merge-base with the public default branch, as the pre-push gate does;
an initial default-branch push scans all ancestry. Unresolved ranges refuse.
No green-run receipt skips code checks or publication checks.

The changed-test subprocess retains its 480-second timeout. The committed
serial file-duration sum plus 60 seconds for setup and
collection is the conservative estimate; a selected file with no recorded time
(a new test file) counts at the median recorded file and still runs. If the
estimate exceeds 600 seconds or pytest infrastructure changes, all guards still run
and changed files outside the guards defer to merge-group pytest. Otherwise the
importing tests fill half of the room the guards and changed tests leave under the cap, never past the 480-second timeout (leaving room for runner variance), cheapest recorded duration first; the
rest defer with the same reason and are listed in `importing_test_files` and
`deferred_files`. The recorded estimate includes the importing tests that run, and
`unknown_duration_files` includes every importing test with no recorded time. Infrastructure
includes conftest, pytest configuration, dependency locks, the CI workflow, CI Python setup,
CI helpers and quarantine inputs. The summary and `pr-affected-proof` artifact
record the candidate, requested files, deferred files and reason, recorded
estimate, reported cases, skips and failures. Deferred test-case counts stay
UNKNOWN because the deferred files were not collected by this job. Workflow
changes use this same deferral path and still execute all listed guards. Invalid
proof reports its stage and exception class; fixed `ValueError` messages also
identify the specific failure without printing event payloads or environment.
Requested files are not a claim that every assertion ran. Normal pytest configuration,
markers, quarantine and governor apply. Hosted duration and the independent
30-day original-failed-head replay remain driver-owned proof requirements.
The initial list includes all six runtime/catalog/global suites from the
original failed group; later PR changes cannot establish old coverage.

The `pr-affected-proof` artifact also contains `pr-repo-wide.json` and
`pr-repo-wide.xml`. The JSON records the exact candidate, marker expression,
requested paths, worker count, subprocess timeout, elapsed wall time,
logical CPU count and initial load average, plus reported cases, failures and
skips. The marker expression requires `repo_wide` and retains the supported
tier's `atlas_release`, `slow` and `site_toolchain` exclusions. It does not
broaden execution to unmarked tests or move nightly or release tests into PR CI.
An empty selection, failed execution, stale report or missing JUnit fails CI.
Both invocations use two pytest workers with work stealing. Invariants have
a 1,500-second subprocess timeout; the combined job has a 40-minute timeout.
The budget uses the hosted measurements on [PR #11922](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/11922):
twice the initial superset's observed marker wall time, rounded up to five minutes, plus the
existing 480-second changed-test ceiling, twice the observed setup time and
one minute for report publication, again rounded up to five minutes.
The same job runs both selections without additional PR jobs or shards.

Every `merge_group` candidate runs the full supported non-slow pytest suite,
frontend toolchain tests and partition audits.
Required full green queue CI gates landing. Nightly `schedule` runs at 03:30 UTC
on `main` and opt-in `workflow_dispatch` runs also execute the full suite.
Other slow tests retain `pytest-slow-nightly.yml`.

Operator approval under the gate freeze, 2026-10-23.

The advisory Hygiene workflow keeps a separate slim environment. Its focused
agent-config tests use pytest, PyYAML, jsonschema and psutil declared in
`requirements.txt`, with direct and transitive dependencies constrained by all
named `==` pins in `requirements-lock.txt` (local path requirements cannot be
constraints).
The shared conftest's Claude adapter pre-import needs jsonschema; its process
guard uses psutil (#10030). Hygiene exposes `packages/v4-runtime/src` through `PYTHONPATH`.
Before executing the focused tests, a `--setup-only` guard collects the same
test set and runs its fixtures: `--collect-only` alone cannot detect missing
dependencies imported during autouse setup. The guard propagates import errors;
`tests/test_hygiene_workflow.py`, run by required CI Gate, also restricts fixture
setup imports to the standard library, repository-local modules and Hygiene's
installed dependency closure resolved through `importlib.metadata`. Other
third-party imports fail even when installed in CI Gate's larger environment.
Negative controls cover unavailable jsonschema and a fixture-time `requests`
import in a scratch copy of the shared conftest. The scratch `tests` package
includes the original package path so newly registered repository plugins remain visible.
Repository imports are classified by their resolved paths (including namespace
packages), with installed site-packages and symlinks outside the checkout excluded.
Direct regression tests cover arbitrary module names and resolved-path boundaries.

| Job | What it does |
| --- | --- |
| Queue commit metadata scan | `merge_group` only. TruffleHog over the queue commit's message, author and committer (below). |
| Secret scan | Event-aware TruffleHog range, OPSEC public-identifier lint, internal-ID check. |
| Checks | PR pytest collection, quarantine admission verification, and `scripts/ci/checks.sh` for every lint and content-contract gate on every tier; fails if any failed. |
| PR changed tests and guards | PRs execute changed test files, tests that import changed files, all explicit guards, and marker-only repository invariants; full tiers exit without duplicate execution. |
| Frontend | Every event. Always runs the real MDX compiler regressions (`-m site_toolchain`); builds and tests the site only when the diff touches the frontend denominator. |
| Refresh pytest durations | Full tier only. Freezes one file-weight snapshot for every shard (below). |
| pytest (1..N) | Full tier only. The full `not atlas_release and not slow and not site_toolchain` suite, split over N static shards. |
| pytest report | Whole-run checks over every shard; records the tested tree, commit, PR and run, then the runner-normalized file durations. |
| CI Gate | `if: always()`; fails on any job result other than the expected one. Also runs the large-file guard and attribution on a sparse, full-history checkout (below). |

`ci-advisory.yml` (pull_request only, never required) carries the advisory
checks: TypeSafe triage (#8232), Atlas POC richness (#3930) and the diff-scoped
Atlas vocabulary coverage report.

For an offline local TruffleHog scan of the work tree or the whole public history
(before a credential, identity, transport or hook change, or after a suspected leak),
see [`secret-scanning.md`](secret-scanning.md).

## Gate inventory

Every gate of the previous `ci.yml` and where it lives now. Only the machinery
that chose *which* tests or checks a change ran is gone.

| Gate | Before | Now |
| --- | --- | --- |
| TruffleHog, event-aware range (`secret_scan_scope.py`) | Secret scan | Secret scan (unchanged) |
| OPSEC public identifiers (`lint_opsec_leaks.py`) | Secret scan | Secret scan (unchanged) |
| Internal IDs (`check_no_internal_ids.py`) | Secret scan | Secret scan (unchanged) |
| Read-only token (`permissions: contents: read`) | workflow | workflow; pytest duration refresh adds `actions: read` |
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
| Frontend build, generated-artifact drift (directly after the build), unit and built-output tests | Frontend, when the denominator matched | Frontend (same denominator, same order); one hydrate and one recorded build, reused only after verification (below) |
| Frontend change denominator incl. backend hydrate inputs | Changes (`classify_changes`) | Frontend scope step (`frontend_change_scope.py`); completeness kept by `tests/test_frontend_denominator_invariant.py` |
| Full non-slow pytest, strict markers, `--timeout=120` | pytest shards (full/selected/docs/content tiers) | pytest shards, full suite on merge-group, nightly and opt-in manual events |
| Postgres tests must not skip (`pg_skip_guard.py`) | per shard | per shard |
| needs_artifact collected set == `registry/artifacts/needs-artifact-expected.txt` | Needs artifact audit (separate `--collect-only`) | pytest report, from each shard's collected list (tests/conftest.py writes it before `-m` deselects) |
| needs_artifact skip set == the same expected set | Needs artifact audit (separate run) | pytest report, from the shards' JUnit |
| Every test file ran | none (planner trust) | pytest report: shard file lists must partition `git ls-files tests` |
| Full-history checkout where tests read old commits | pytest, Fast checks, Contracts | pytest shard 1 (the history shard), Checks, Frontend, Secret scan; pytest shards 2..N are shallow |
| Queue commit metadata (message, author, committer) scanned for secrets | Secret scan, every queue run | Secret scan on a full queue run; Queue commit metadata scan on every queue run |
| TypeSafe triage (advisory) | Fast checks, `continue-on-error` | `ci-advisory.yml` (not required) |
| Atlas POC richness, vocabulary coverage (advisory) | Contracts, `continue-on-error` | `ci-advisory.yml` (not required) |
| Other slow tests, quarantine run, flake ledger, failure issue | `pytest-slow-nightly.yml` | unchanged |

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

`scripts/ci/gate.py` parses the event JSON and checks the checkout against
`GITHUB_SHA`, the event ref, action and candidate identity. Unknown events,
missing metadata, incorrect refs and malformed proof fail closed.

The gate requires Secret scan, Checks, Dependency audit, Frontend and PR changed tests and guards to
succeed on every event. Duration refresh, pytest and pytest report must succeed on the
full tier and be skipped on PR admission. Queue commit metadata scanning must
succeed on merge-group events and be skipped elsewhere. Every other result,
including cancellation or unknown status, blocks the gate. `always()` ensures
it reports after failed or cancelled dependencies.

Queue runs never reuse PR results. The tested-tree artifact remains an audit
record of the candidate and its partition results.

The gate's checkout keeps full history but is sparse (`scripts/` and
`.python-version`). `actions/checkout` then fetches with `filter: blob:none`, so
it downloads commits and trees, not the 700 MB working tree: in run
40633770801 the full checkout took 29 s, and 4 min 06 s in the outlier run
40610924205. The large-file guard sizes every added or modified blob as before;
`check_large_files.py` first fetches the blobs the partial clone lacks in one
request, instead of one round trip per blob. Attribution reads commits and
fetches PR heads exactly as before; `merge-tree` fetches any blob it needs.

The queue metadata job publishes `ci-queue-candidate`, binding the event's original
base and candidate to the workflow run and attempt. For recovery, compare these
immutable SHAs, then inspect that complete base-to-head diff against the failing tests, code,
fixtures, dependencies, configuration and workflow. This includes every grouped
change without guessing membership. Include `queue_group_diff` with `base_sha`,
`head_sha` and the sorted `paths` list in the existing recovery evidence comment.
Include old and new names for renames. The publisher verifies this against the
same-run artifact and GitHub comparison before mutation; missing, inconsistent or capped file lists
block recovery. Matching failed jobs across PRs alone cannot prove a service
failure. The existing one-attempt allowance and green-head/review gates remain.

Before switching, the driver must consume the independent measurement author's
frozen last-50 baseline and declaration. The denominator is the next 50
consecutive non-draft PRs with exclusions declared beforehand. Report median
open-to-merged against the 20-minute target and p90, plus baseline comparisons
for defect ejections, red-main incidents, review rounds and queue-CI p90.
If PR-caused ejections exceed 10% of enqueues or an attributable main break
occurs, revert this change with one clean PR. Source transmission is not
measurement proof; the driver owns the declaration dependency and observation.

## Frontend: one hydrate, one recorded build (#9718)

The Frontend step runs `npm run hydrate` once, then
`site/tests/helpers/ci-build-artifact.ts record` runs `astro build` once. The
record (under `$RUNNER_TEMP`) keeps the complete build log and exit code, writes a
fresh nonce into `dist/`, and stores the input identity: HEAD, the tracked
working-tree diff and the content hash of every file under `site/src/data`,
`site/public` and `data/atlas.db`, taken before the build. The build may only
add inputs: `astro.config.mjs` creates the fallback
`site/public/audio/pronunciation/manifest.json` when it is absent, as on a fresh
runner. Such a file is hashed after the build, listed in the record's
`buildCreatedInputs` and printed as `build created input: …`. A build that
changes or removes an existing input fails verification. A failed build fails
the step at once.

The generated-artifact drift check runs directly after the build. Then:

1. `npm run test:unit:ci` verifies the record, then runs the same Vitest
   selection and excludes as `test:unit`, without a second hydrate, with
   `--fileParallelism --maxWorkers=3`. Three workers leave one of the runner's
   four vCPUs to the Vitest main process, matching Vitest's own default of the
   CPU count minus one. Every test file still runs in its own isolated worker.
2. `ci-build-artifact.ts verify` runs again, so an input a unit test changed
   fails here.
3. `npm run test:built-output` runs with `FRONTEND_BUILD_RECORD` set.
   `build-renders.test.ts` verifies the record and runs its original assertions
   on the recorded log and `dist/`, without rebuilding.

Verification fails if the record, log or `dist/` is missing, the log hash or the
`dist/` nonce differs, the build exited non-zero, or any input changed. It never
falls back to a rebuild. Without `FRONTEND_BUILD_RECORD`, `npm test`,
`npm run test:unit` and `npm run test:built-output` behave as before:
self-contained, with their own hydrate and build. Outside `test:unit:ci`, unit
test files still run one at a time (`fileParallelism: false` in
`site/vitest.config.ts`), and `test:built-output` always does.

Parallel unit files must not write shared paths. The Atlas fixture parity tests
give `SqliteAtlasDataSource` a private empty `searchArtifactsDir` instead of
hiding `site/src/data/lexicon-search-*.json` (#9850). Other unit files write only
under their own temporary directories. The exception is
`ActivityKit.contract.test.tsx`, which regenerates the `*.generated.ts` type
files; those are imported only with `import type`, which the compiler erases.

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
- Weights never change which files run; a wrong weight only costs balance.
  `Refresh pytest durations` takes the median of the last five successful
  merge-group `pytest-file-durations` artifacts (downloaded concurrently),
  keeping committed weights for files they do not name, and every shard reads
  that one snapshot.
- Hosted runners differ in speed. In run 40633770801 seven shards ran their
  files at 0.56–0.72x their usual seconds and seventeen at 0.88–1.11x, so raw
  seconds recorded the runner as much as the test. Each shard therefore writes
  the weights it was split with (`split --weights-out`) into its artifact, and
  `pytest report` records `durations --shards`: each shard's seconds divided by
  that shard's speed, the median observed/expected ratio over its files with at
  least 2 s of weight (1.0 when fewer than ten qualify, e.g. a shard holding one
  large file). The report log prints every shard's speed. A listed file that ran
  no test records 0, so files the tier deselects (the nightly `slow` groups in
  `tests/conftest.py`) stop carrying weight. The slowest shard still depends on
  which runner it draws; static splitting cannot know that in advance.
- To rebuild the committed file from one full run:

  ```bash
  gh run download <run-id> --pattern 'pytest-junit-shard-*' --dir /tmp/junit
  .venv/bin/python -m scripts.ci.split_tests durations --shards /tmp/junit > scripts/ci/pytest-file-durations.json
  ```

### History shard

Eight test files are listed in `scripts/ci/history-tests.txt`. All eight read old
commits: `git ls-tree`/`git show`/`git cat-file` of an old SHA, a recorded historical
commit, a frozen base commit, and `origin/main` ancestry. On a shallow checkout,
fetching `main` from GitHub downloads all of main's history, 65-77
s per test instead of 0.3 s. `split_tests.py` pins the listed files to shard 1
and balances the other files around them. Shard 1 is the only shard checked out
with full history (`fetch-depth: 0`), a full clone with every blob (see
"Full-history checkouts are blobless" below). Shards 2..N check out only the tested
commit (`fetch-depth: 1`) and run pytest with `GIT_ALLOW_PROTOCOL=file`. A
listed file that is no longer tracked fails the split.

The list is measured, not guessed. Run 36654595606 had every shard shallow
with network git blocked in the pytest step. It was compared test by test with
the full-history run 36650655215. Only seven files changed outcome (28
tests, passed to failed). The one other change is a `test_ci_split` workflow
assertion that failed on the experiment's own `GIT_ALLOW_PROTOCOL` edit. None of them skipped:
each failed loudly, with git exit 128 or a blocked https transport. Without the
block, the network fetch in the two delegate tests pulled main's history into
their shard and hid two of the five history files. A new test that needs
history or fetches from GitHub therefore fails on a shallow shard; add its file
to the list.

To change the shard count, edit the static `matrix.shard` list (it must stay
`1..N`). `scripts/ci/slot_inventory.py --check` (actionlint workflow) counts
every PR-path job against the slot ceiling set in that script, which keeps a
margin for incident response. It counts each workflow's jobs once, as if one
run of each were in flight. It does not model overlapping runs, such as
several merge-queue builds next to PR CI and other workflows. A passing
inventory is therefore not proof of capacity for a build-concurrency change;
see D3 in [`ci-speed-program.md`](../epics/ci-speed-program.md).

### Full-history checkouts are blobless (FR-58)

The public pack is about 8 GB, nearly all of it old file contents. Commits and
trees for the whole history are about 30 MB. A `fetch-depth: 0` checkout in
`.github/workflows/` therefore also sets `filter: blob:none`: it downloads all
commits and trees, plus the blobs of the checked-out tree. Ancestry checks,
merge bases and changed-file lists read commits and trees only. A step that
reads an old file's content (`git show <rev>:<path>`, a content diff) makes git
fetch the missing blobs from GitHub; `git diff` and `git log --patch` fetch
them in one batch per command. CI Gate gets the same filter from its sparse
checkout. Before this change, one checkout took 16 s to 424 s, and the
5-minute jobs were cancelled at their limit.

Jobs that run test files keep a full clone: pytest shard 1, coverage-ref shard
1, pytest-slow-nightly, and PR changed tests and guards on `pull_request`.
`tests/test_storage_classification_table.py` sizes 1,706 `data/` blobs (about
1 GB) at a frozen base with one `git cat-file -s` each. In a blobless clone each
is a separate fetch, and in run 40762542278 the test hit its 120 s timeout. In
a merge group, PR changed tests and guards runs no tests, so it is blobless there.

TruffleHog cannot use this checkout as before: its own `git clone` of a partial
clone fails. Both scan jobs fetch and verify the blobs of their range first and
scan in place; see
[secret-scanning.md](secret-scanning.md#blobless-ci-checkout-fr-58). The
`full-history-audit` dispatch keeps a full clone.

## Shard setup

Per shard: checkout (shallow; full history on the history shard), Python
3.12.15, then `scripts/ci/test_env.sh start` runs `npm ci` and
`scripts/ci/start_postgres.sh` (bubblewrap, PostgreSQL 16 cluster, DSN
verification) in the background while `python-ci-env` installs the locked
environment from main's exact-key uv cache; `test_env.sh wait` fails the job if
either background task failed. A container image was not adopted: the checkout
cannot be inside an image, and pulling a prebuilt environment of this size
costs about what the cache restore does (see the measurements in the ci-v3 PR).

All Python workflow jobs read the repository's `.python-version` with
`setup-python`'s `python-version-file`. The shared composite reads the same
file for setup-uv's explicit `python-version`, so local environments, the
cache reader and the cache writer agree. Keep `check-latest` disabled (the
default). A pin update changes the uv key; until main warms that key, the
composite's online install fallback handles the miss. The #9062 measurement
on hosted image `20260920.314` found 3.12.14 already cached, while 3.12.8
required a download on every shard.

The history shard keeps full Git history: eight pinned test files read history
(listed in `scripts/ci/history-tests.txt`, consumed
by `scripts/ci/split_tests.py`).
Other shards are shallow. #9211 rejected blobless checkout because those
history readers need the committed blobs as well as the commit graph.

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

## Advisory component shadow (#9721 slice 6)

`Component shadow (advisory)` is a separate report-only job after pytest, including red
runs. It checks out the event head with full history, reads the full-run shard
artifacts, and uploads an ignored `component-shadow` JSON receipt. Its failures
are advisory and absent from CI Gate's result checks. The full pytest command,
static shards, full tested-tree record, partition checks and needs_artifact
reconciliation remain unchanged. This does not authorize PR narrowing; decision
A in `plans/component-separation-9721.md` and slice 7 remain separate.

The shadow uses the event base/head merge-base diff, including stacked parent
commits and both rename sides. Empty/missing/unresolvable diffs, non-PR events,
workflow/tool/dependency/shared changes and unresolved runtime edges select all.
Resolved would-run files come from `components.test_files`, including importers
and shared integration obligations. Literal file reads and Python subprocess
targets contribute reverse edges; unknown reads/argv and sys.path changes select
all. The receipt records changed paths, selected nodes/files, would-skip files,
full JUnit failures, collection errors, tool/source/graph identities and artifact
coverage problems. Collected IDs are those attested by full-run JUnit plus the
existing pre-deselection needs_artifact lists; JUnit cannot attest other IDs
removed by the existing marker filter. Executed IDs exclude skips and collection
errors. No separate collection or candidate test execution is introduced.

The review of record measured 14,692 unresolved edges at
`c3695226db3b18ec0e3ab42c9a7a3221e00df69c`: 10,379 file reads, 2,427 subprocess
calls, 1,641 `sys.path` edges, 240 dynamic loads and 5 missing imports. Receipts
retain this attributed baseline as `review_unresolved_edge_census`, separately
from their current `unresolved_edges`. Any unresolved edge forces full selection;
this census therefore demonstrates a narrowing gap, not successful narrowing.
Resolving those edges is a separate follow-up owned by the #9721 driver.

Use the task-prescribed interpreter as `$P` and ignored, managed scratch as `$R`:

```bash
# Run/job metadata census only, before observing candidate selection/results.
"$P" -m scripts.ci.component_shadow inventory --output "$R/baseline.json"
"$P" -m scripts.ci.component_shadow register --baseline "$R/baseline.json" \
  --minimum-narrowed-cases 1 --output "$R/registration.json"
# After registration, acquire the complete live census through the stop date.
"$P" -m scripts.ci.component_shadow inventory --first-attempts --created "$START..$STOP" \
  --output "$R/receipts/runs.json"
"$P" -m scripts.ci.component_shadow check --registration "$R/registration.json" \
  --receipts "$R/receipts"
```

Registration refuses overwriting an existing file. It freezes the graph, source
and tool hashes; all pytest-red PR/merge-group run IDs in the plan's baseline
window (2026-10-03 through 2026-10-06 11:14:28 UTC); and the next 150 completed
PR runs whose first attempt completes after registration, with at least
30 pytest-red runs. Order is completion time then numeric run ID. Cancelled or artifact-less
completed cases are included and remain unresolved. A paginated live run/job
census is required: missing receipts cannot shrink the denominator. Run attempts
beyond the first do not enter the live window. The live census uses attempt-1
run and job metadata, so later reruns cannot erase first-attempt red cases.
Choose `$START` early enough to include PR runs already in flight at
registration; they count when their first attempt completes afterward. Metadata
acquisition reads job conclusions, never candidate test IDs or artifacts.
Registration also freezes a positive `minimum_narrowed_cases` (default 1;
raise it with `register --minimum-narrowed-cases` before observing results).
The checker reports narrowed red and injected case counts separately and their
sum. Only valid, oracle-verified registered historical red cases, live pytest-red
cases and injected controls in `selected` mode with a non-empty would-skip set
count; green live runs and full selections do not. A zero count or a count below
the frozen minimum stays unresolved with non-zero exit, even with zero misses.
An absent or invalid registered minimum also stays unresolved. This minimum
prevents a vacuous pass; it is not approval to narrow PR execution.

Every skipped full-JUnit failing ID is a miss, including flaky tests. The sole
test-failure exemption is the same ID failing in an artifact-complete, first
attempt rerun of the event base commit under the registered tools. Produce that
receipt using `report --kind base --candidate-run-id ID --head BASE_SHA` against
its full-run artifacts. The base rule is frozen before candidates; no post-hoc
flaky reclassification is accepted. A collection error outside selection always
counts. Historical replay uses `report --kind historical --run-id ID` after
registration; historical observation timestamps need not follow registration.
Run the registered observer with `--root` pointing at the historical source
checkout: its map/tool identities come from the observer, and its source census
comes from that checkout, which may predate the tools.
Live receipts observed before registration are refused. Keep each receipt at
`receipts/ID.json` and its original XML files under `receipts/ID/junit/`
(subdirectories are allowed); base reruns use their own run ID. The checker
re-reads and hashes those files independently and refuses a disagreement with
the receipt. The shadow artifact retains the receipt and original shard
artifacts for 45 days, covering the 30-day live window.

The driver supplies and freezes `injected_cases` separately, recording an ID,
`coverage` labels, `expected_failure_ids` and a `registered_at` timestamp for
each before observing its results. At least twelve distinct controls cover all eight nodes and the
shared-fixture, dynamic-load, subprocess and stale-artifact classes. The author
must not supply those held-out faults. The checker cannot pass until these
controls, every historical replay and the live denominators are complete with
zero misses. Every injected control must demonstrate its pre-registered failing
IDs in the full JUnit. Missing, unreproducible, malformed, mismatched-tool or
artifact-less cases remain unresolved. Receipts observed after day 30 cannot
complete the window. After day 30 an incomplete window is inconclusive,
with the missing-evidence residual owned by the driver; it never authorizes
narrowing.

Cost is unknown until matched measurements are supplied via `report --cost`.
CI passes `--cost-unknown-reason
matched-pr-queue-measurements-not-available-in-shard-artifacts` because shard
artifacts contain test durations, not matched full PR/queue runner costs, reuse
probability or all overheads. Receipts retain that reason rather than inventing
cost inputs. The driver owns acquisition of matched measurements before decision A.
Inputs are `full_pr_runner_minutes`, `full_queue_runner_minutes`,
`reuse_probability`, `reporter_runner_minutes`, `rerun_runner_minutes`,
`ejection_runner_minutes`, `duplicated_preparation_runner_minutes` and
`elapsed_wait_minutes`. The projection scales PR cost by selected JUnit test
time and adds expected queue execution and every supplied overhead. Both baseline
and candidate use `(1 - reuse_probability) * full_queue_runner_minutes`.
Runner-minutes and elapsed waits are separate, and projection is not a measured
saving. The historical shadow cost model retains `lost_reuse_runner_minutes` as
zero; PR-run reuse is retired. The existing
`projected_cost_after_lost_reuse` receipt key is retained for reader compatibility.
The driver must measure combined PR/queue cost before decision A; the retired reuse path cannot supply current proof.

CI recovery uses one durable Git-common-directory `ci-recovery.sqlite3` record per
repository/PR/head on each host for both failed-job reruns and keeper/direct
re-enqueue. Before recovery, post
`<!-- ci-recovery-evidence {"pr":42,"head":"<PR SHA>","run_id":123,"job_ids":[456],"tested_sha":"<tested SHA>","failure_evidence":"<failure evidence>","unrelated_to_diff":"<diff diagnosis>"} -->`
on the PR. All failing job IDs are required. Evidence must be posted by the
authenticated login with OWNER, MEMBER or COLLABORATOR association, matching
the verdict author filter. Retain any keeper requeue grant.

The publisher pages through all GitHub `RemovedFromMergeQueueEvent.beforeCommit.oid`
values, using `pageInfo` rather than `totalCount` to establish completeness.
Manual, `merge_conflict` and `behind` removals are exempt from CI recovery, including at
the current head and with a null commit; manual removals include keeper revocations.
Other removals naming the current head make enqueue a recovery. CI removals
(`failed_checks` or `timeout`) with a null commit always count as at-head.
Force-push history cannot clear a null-commit CI removal, including a force-push
to another SHA followed by a fast-forward back to the current head. These recognized reasons
accept both uppercase and lowercase values. Unknown null-commit reasons require
recovery evidence and consume the allowance rather than blocking recovery as
unreadable data. Removals only at other heads permit normal initial enqueue
without spending the new head's allowance.
Only an explicit different `beforeCommit.oid` establishes a removal at another head.
Before normal initial enqueue, the publisher also checks the
durable record for a prior re-enqueue at that head; a branch-run rerun alone
does not block initial enqueue. Returning to the same SHA never refunds a spent
recovery allowance, even when the latest removal names another head.
Truncated, unreadable or ambiguous GitHub removal data refuses enqueue with
`RECOVERY_REMOVAL_UNKNOWN`; restore the complete read before retrying.
Failed push runs on `main`, scheduled runs and other runs without a PR retain
normal failed-job rerun behavior. Ambiguous PR or
merge-group associations remain refused.

A spent allowance has two ways out: a new PR head with fresh exact-head approval
and green CI, or an attributed operator action. Record an operator-authorized
exception as a separate attributed PR comment naming the exact head, first
attempt and authorization. The exception comment does not itself unblock the
tools, erase or reset the shared record, or grant an automatic bypass; any
exceptional action remains the operator's responsibility. One workflow run per
PR head can be rerun, and reservations are not refunded after a crash or uncertain
transport. The legacy-table edge case fails closed. These limits remain
documented residuals, not additional recovery paths.
