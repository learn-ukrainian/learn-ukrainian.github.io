# CI Gate

New workflow (Fable 5.1, 2026-09-03). `.github/workflows/ci.yml` is a short
replacement, not the old two-tier merge-queue file.

`CI Gate` is the only required GitHub check. Same jobs on `pull_request` and
`merge_group`. Inside Fast checks, the Preflight step runs on `pull_request`
only.

| Job | When |
| --- | --- |
| Changes | always (`docs_only` / `docs_reads_content` / `frontend` / `shards` / `pytest_mode` / `shard_count` / `pytest_candidates` / `preflight`) |
| Secret scan | always |
| Fast checks | always; one runner for four check steps, in this order (see [Fast checks](#fast-checks-8750-phase-a2)): |
| Fast checks: Preflight step | `pull_request` in the `full` or `selected` tier (`preflight=true`): the `repo_wide` set plus the registered extra tests, in parallel with the shards (see below) |
| Fast checks: Ruff step | not docs-only |
| Fast checks: Plan Validate step | always (the v2 plan validator self-scopes on `pull_request` to its input paths; the generated arc landing `a1 --check` always runs) |
| Fast checks: TypeSafe triage step | always (advisory during soak, #8232: `continue-on-error`, and CI Gate accepts any outcome, so a red TypeSafe step is visible but does not fail the gate. Missing `TYPESAFE_API_KEY`, API/transport errors and malformed responses skip green; only a `broken` verdict with choice confidence or `high_risk` >= 0.8 turns the step red) |
| pytest | always (`full` → 10 shards; `selected` → 1 shard over candidates plus the `repo_wide` tests; `docs` → 1 `docs_skills` shard plus the `repo_wide` tests, plus the `reads_content` tests when the change touches `curriculum/` or `wiki/`; `content` → 1 shard: `-m 'reads_content and not slow and not atlas_release'` `--timeout=120` + shard safety net) |
| Contracts | not docs-only |
| Frontend | when frontend paths changed (always on for the content class: content renders through the site build) |
| CI Gate | always |

The Changes job uses `scripts/ci/classify_changes.py`. The `full` Python tier
runs every required Python test except `slow` and `atlas_release`; those run
only nightly. Ordinary PRs skip ruff/contracts and run one `docs_skills` pytest
leg only when every path is Markdown in docs/, shared skills, agent deploy
trees, or the repository root,
or belongs to curriculum/ or wiki/ without a `site/` path (the curriculum/wiki
fast path predates the content class).
Frontend denominator matches always override the docs exemption, including
`packages/activity-kit/`. Unknown paths, including Markdown under unrecognized
or executable trees, run the full pytest shard set and ruff/contracts;
frontend follows its denominator. All docs YAML, schemas, packages, dashboards,
dependency manifests/locks, Python/pre-commit configuration, and scripts/config
or scripts/ci changes therefore run the full PR-tier floor.

Content class (#8399): learner content under `curriculum/l2-uk-en/`,
`curriculum/l2-uk-direct/`, `site/src/content/docs/`, or `wiki/`, minus the
code-imported files inside those roots (each forces full on both events and
is excluded from the docs exemption): any `curriculum/**/curriculum.yaml`,
`curriculum/l2-uk-direct/manifest.yaml`,
`curriculum/l2-uk-direct/bolshakova-letter-order.yaml`,
`curriculum/l2-uk-en/module-mapping.json`, `curriculum/l2-uk-en/vocabulary.db`,
and any `*.py`/`*.db`/`*.sqlite` or track-root `*.json` under the roots (the
importers are listed in `is_code_load_bearing_content`'s docstring). The
events then differ deliberately:

- **pull_request**: the content class applies only when every changed path is
  content class AND at least one is `site/src/content/docs/**` — the case
  that used to fall to full because `frontend` was true (PR #8384). A PR
  touching only `curriculum/**`/`wiki/**` keeps the docs fast path.
- **merge_group**: each queue entry uses its own changed paths (ALLGREEN).
  Docs-only changes run the full required Python tier because tests can read
  docs through dynamically constructed paths. Curriculum/wiki-only entries
  keep their `docs` class with the `reads_content` leg; learner-page content
  keeps its `content` class. Frontend-only changes run the full
  required Python tier because Python tests read `site/` and
  `packages/activity-kit/` files. Any other change, including Python source,
  tests, workflows, dependencies, mixed classes, and uncertain paths, runs
  `full` before reaching `main`.
  Code files under broad curriculum/wiki docs roots, and Python or shell files
  under frontend roots, also run `full` even if they previously entered a
  narrower class.
  Frontend still follows its existing path denominator; `full` does not
  automatically turn on the Frontend job. Lookup failures resolve to `full`.

| Changed-path class | `pull_request` Python tier | `merge_group` Python tier | Frontend job |
| --- | --- | --- | --- |
| Docs-only | `docs` | `full` | off |
| Content-only learner pages | `content` | `content` | on |
| Curriculum/wiki without learner pages | `docs` | `docs` | off |
| Docs mixed with curriculum/wiki | `docs` | `full` | off |
| Frontend-only `site/` or `packages/activity-kit/` | none | `full` | on when in denominator |
| Code, other mixed classes, or uncertain | selected or `full` | `full` | existing denominator |

The docs lane runs marked `docs_skills` and `repo_wide` tests, plus
`reads_content` for curriculum/wiki edits. The content lane runs marked
`reads_content` tests. The queue runs `full` for every docs-only entry,
including dynamically constructed test reads. Their PR path class remains
`docs`.

The content class emits `pytest_mode=content`: one shard running
`-m 'reads_content and not slow and not atlas_release'` (same filters and
`--timeout=120` as the full PR tier) plus the non-slow tests in
`tests/test_ci_shard_partition.py`,
with Ruff, Contracts and the Frontend build still on (`docs_only=false`,
`frontend=true`). The marker is load-bearing:
`tests/test_reads_content_marker_invariant.py` fails when a test module
references those content roots without carrying `reads_content`, so new
content-reading tests cannot silently fall out of the class.

**Runner-slot budget (#8876).** `scripts.ci.slot_inventory --check` expands
every PR-path workflow. Its dynamic `ci.yml` pytest matrix uses the full-tier
default from that workflow's `env.PYTEST_SHARD_COUNT`; an unreadable default
fails the check. The current inventory is 32 jobs, including 10 pytest shards
and 17 jobs in `ci.yml`. On the GitHub Team plan, 60 hosted jobs can run
concurrently. The inventory ceiling is 58 = 60 - 2 reserved slots. Two
overlapping full `ci.yml` workflows use at most 2 × 17 = 34 slots, leaving
24 for other PR workflows plus two reserved slots. The 32-job inventory is a
sum across workflows, not a simultaneous peak: if every job in two copies were
runnable together, 2 × 32 = 64 would exceed 60 and some jobs would queue.

CI runs on `pull_request` opened/synchronize/reopened; labels and PR-body
edits do not start it. `full-ci` is read from the PR's current labels
(case-insensitive, fail closed) on the next PR push and in every merge-queue
run, where every PR in the group is resolved from the queue refs. A label added
after a green PR run does not rerun it: push again, or rely on the merge queue.
Use the label only when a change affects tests the path classifier cannot see;
explain that blind spot in the PR. It forces the full Python tier while known
changed paths still decide whether Frontend runs. The merge queue already runs
the full Python tier for code, frontend-only, and docs changes outside
curriculum/wiki (#9073).
Manual runs and the daily 03:30 UTC schedule in `ci.yml` use that same full
floor (`not atlas_release and not slow`). `pytest-slow-nightly.yml` remains the
separate slow selection; this adds no retries or duplicate slow-test execution.
Missing/malformed comparison data, API errors, empty changes, and the compare
API's 300-file cap fail closed to the full tier including frontend.

Scripts/`tests/`-only PRs that pass the selected allowlist run
`pytest_mode=selected`: one matrix job, `shard_count=1`, and `plan-files`
stdin from `pytest_candidates` (resolved once in Changes — no re-derive in
pytest). Shared-root denylist hits (`.github/`, `scripts/ci|config|build/`,
conftest, locks, packages/schemas/site/curriculum, etc.), non-test files under
`tests/`, non-`.py` under `scripts/`, stem collisions, unmapped scripts, deleted
test files, empty or ≥80 candidates, and anything outside the allowlist stay
`pytest_mode=full` with ten shards. A selected PR runs `full` on its
`merge_group` entry. Contracts and ruff stay on whenever
`docs_only=false`. After merge, the CI stream owner tracks one week of
`ci_timings` on the private work item (selected may be rare under on-disk stem
collision conservatism).

## Repo-wide tests always run in the selected and docs tiers (#8707)

Import selection can never pick a test that scans the repository's own trees:
the Changes job links a changed `scripts/foo.py` to `tests/**/test_foo*.py` (and
a changed `tests/test_x.py` to itself), but a test scanning `tests/` or
`scripts/` has no import edge to the changed module. That is how PR #8692
merged green on the selected tier and then turned `main` red on shard 3 for
every full-tier run: `tests/test_lint_test_assertions.py::test_repo_test_suite_is_clean`
scans all of `tests/` and was never selected for a `tests/orchestration/test_thread_handoff.py`
change.

Such tests carry the `repo_wide` marker (registered in `pyproject.toml`). After
the candidate run, a `selected` shard runs the marked set under its own narrow
allowlist:

```
git ls-files -- tests | grep -E '/test_[^/]+\.py$' \
  | xargs -r grep -lE 'pytest\.mark\.repo_wide' | sort
LU_PYTEST_SHARD_FILES=<that list> pytest tests \
  -m 'repo_wide and not slow and not atlas_release' -n logical --dist=loadfile ...
```

The narrow allowlist keeps collection cheap (the full tree is ~2 minutes to
collect); the known set currently runs ~400 tests in under two minutes. An
empty list fails the step loudly. The grep matches the exact marker
declaration, not a bare `repo_wide` mention, so a comment or an unrelated
string cannot pull a file into the allowlist (the `-m` filter would skip it
anyway, but the list stays honest).

The **docs lane** runs the same `-m repo_wide` invocation after its
`docs_skills` run. Docs-lane PRs reach no other pytest leg, and several
repo-wide scanners read `docs/`: `tests/test_work_privacy.py`,
`tests/test_agent_fleet_tooling_guardrails.py`, and
`tests/test_public_tree_no_baked_host_run_root.py`. A docs-only PR that adds a
baked host path under `docs/` is therefore caught before merge.

The **content lane** deliberately runs no `-m repo_wide` leg: content mode runs
`-m 'reads_content and not slow and not atlas_release'` (plus the shard safety
net), so a scanner of a content root is selected by its `reads_content` marker
without a repo-wide pass. Which lane a content-only PR reaches decides whether
that marker is enough:

- A PR whose paths are all content-class and include a `site/src/content/docs/`
  path lands on the **content lane**, which runs `reads_content`: scanners of
  that tree, for example `tests/test_site_links.py`, run here.
- A PR touching only `curriculum/` or `wiki/` — no `site/src/content/docs/`
  path — is docs-only and lands on the **docs lane**. Since #8720 the docs lane
  also runs `-m 'reads_content and not slow and not atlas_release'` (under the
  same narrow allowlist as the `repo_wide` leg) whenever the flag
  `docs_reads_content` is `true`, which `classify_changes.py` sets only for a
  docs-lane result with some path under `curriculum/` or `wiki/`. This closes
  the gap that let PR #8712 (a docs-only change) merge green and turn `main`
  red on the next full-tier run: `docs/epics/fresh-build-build-program.md` is a
  hashed source of every `curriculum/l2-uk-en/lesson-plans/<lvl>/_decisions.yaml`,
  and `tests/curriculum/arc/test_decisions_record.py` (a `reads_content` module)
  went red on `main`. A few curriculum and wiki scanners are marked `repo_wide`
  and ran there before #8720: `tests/test_ohoiko_source_inventory_scope.py`,
  `tests/test_prompt_template_render.py`, `tests/test_a1_review_scores.py`,
  `tests/test_aggregate_findings.py`, `tests/test_schema_validation.py`
  (`test_a2_plans_match_module_schema`), and the reference checks in
  `tests/test_skill_instruction_routes.py`; the new `reads_content` leg is what
  covers the rest.

Repo-wide tests that read a content tree and must also run on the content lane
carry `reads_content` as well: `tests/test_llm_reviewer_dispatch.py`,
`tests/test_threshold_source_of_truth.py`, `tests/test_sparse_collection_guard.py`,
`tests/test_public_tree_no_baked_host_run_root.py`,
`tests/api/test_app_factory.py`, and
`tests/test_curriculum_upgrade_no_host_run_root.py` are marked both ways, and
none is `slow`/`atlas_release`.

`tests/test_repo_wide_marker_invariant.py` keeps the marker honest. Marker
detection is syntactic and per-function (AST): a test counts only when its own
`@pytest.mark.repo_wide` decorator, its class decorator, or a module-level
`pytestmark` contains `pytest.mark.repo_wide`, so decorator order and comments
do not matter and a module with two scanners and one marker fails. The
authoritative guarantee is the explicit registry of known repo-wide
modules/functions plus a reasoned `NOT_REPO_WIDE` escape hatch; the AST
heuristic over each test module (repo-rooted `.glob`/`.rglob`,
`os.walk`/`os.scandir`, `git ls-files`/`ls-tree` through `subprocess`, and
known whole-tree linters, propagated through helper calls) is a best-effort
net. The invariant also fails when the selected tier or the docs lane drops
its `-m repo_wide` invocation.

No CF attest. No auto-arm. No landing-class classifier. No coverage floor.
Red team review is out of band.

## Early PR preflight (#8750 phase A)

The Preflight step of the `Fast checks` job reports a broken repo-wide invariant (a missing
`subprocess` timeout, the test-assertion lint, the marker invariants) in a few
minutes instead of after a full pytest shard. Before it, the p50 time to the
first failed job on a full PR run was about 13 minutes.

### Measured results (2026-09-25)

Baseline before phase A (459 CI runs, 2026-09-22 20:24Z to 2026-09-24 23:07Z):
89% of PR runs take the full tier; time to first failed job on failing full PR
runs p50 13.0 min, p95 29.2 min; pytest job queue p50 1.2 min, p95 12.7 min.

Held-out probe PR #8759 (a timeout-less `subprocess.run`): the preflight failed
on `tests/test_subprocess_timeout_guard.py::test_no_unallowlisted_timeout_less_subprocess_calls_under_scripts`
after 3m04s of execution; it waited 5m21s for a runner; its verdict came 10m12s
after the run started; `CI Gate` was red; the shards' repo_wide backstop also
failed.

Known limit at the time of this measurement: the preflight competed with the
pytest shards for GitHub-hosted runners at the former 20-job Free-plan cap, so
queue time could dominate. Phase A.2 (issue #8750) consolidated short checks
into one `fast-checks` job. The organization moved to the 60-job Team plan on
2026-09-27; the historical queue measurements above predate that change.

**When it runs.** `scripts/ci/classify_changes.py` decides once and emits
`preflight`. `preflight_for()` returns `true` only for a `pull_request` event
whose tier is `full` or `selected`: the tiers whose shards run the
`repo_wide` set. The Preflight step's `if:` (and its setup steps') and CI
Gate both read that one output, and nothing in `ci.yml` re-derives it. The other lanes get no
preflight:

- The **docs** lane already runs `repo_wide` in its single short shard.
- The **content** and **frontend** lanes do not run `repo_wide` at all, so a
  preflight there would change what the gate proves.
- **`merge_group`, `schedule` and `workflow_dispatch`** always get
  `preflight=false`.

A `full-ci` label or a classifier failure on a PR forces `full`, and so turns
preflight on.

**What it runs.** It uses the same allowlist construction and flags as the
shards' `repo_wide` leg. An empty allowlist fails the step loudly:

```
LU_PYTEST_SHARD_FILES=<repo_wide list> pytest tests \
  -m 'repo_wide and not slow and not atlas_release' --strict-markers \
  -n logical --dist=loadfile --max-worker-restart=0 --timeout=120 \
  --timeout-method=thread --override-ini addopts=-v
```

A second invocation then runs the files registered in the step's
`PREFLIGHT_EXTRA_TESTS` env, one path per line, under
`-m 'not slow and not atlas_release'` with the same flags. These are cheap
invariants that fail often but are not `repo_wide`. Today the list holds only
`tests/curriculum/arc/test_decisions_record.py`, the cross-file hash
invariant that caused 7 of the 40 sampled PR failures. On its own it takes
about 5 s. An empty list also fails loudly. `tests/test_ci_preflight.py`
checks that every registered path exists and is not already `repo_wide`.
Both invocations always run, so one run reports every broken invariant; the
step fails if either one failed.

**Setup.** Preflight uses the same Python and uv install as the shards, and
the same Atlas manifest hydrate. It leaves out the Postgres service, Node/npm
and the native apt packages (bubblewrap, libpq, apparmor), because no
`repo_wide` test uses them: no marked file mentions a Postgres DSN,
`psycopg` or `bwrap`, and the one that mentions `npm` stubs it. The whole
selection passes in a fresh depth-1 clone with no Postgres DSN and no
`node_modules` (the shared Fast checks checkout is full-history because
Plan Validate and TypeSafe triage need it). The uv setup, dependency install
and hydrate steps run only when `preflight=true`. Step
`timeout-minutes: 8`.

**Parallel, not gating.** No shard `needs: fast-checks`, and the shards still
run the `repo_wide` tests as the backstop, so a green run is no slower.
Nothing is cancelled when preflight fails. Preflight only makes the red
signal arrive earlier.

**CI Gate rule.** This rule lives in the gate step:

- `preflight=true`: the Preflight step outcome must be `success`. `failure`,
  `cancelled`, `skipped` and a missing output all fail the gate.
- `preflight=false`: the Preflight step outcome must be `skipped`.
- If Changes itself did not succeed, the gate fails before it reaches this
  rule.

`merge_group` and nightly runs have no preflight. Their gate evaluation is
unchanged apart from the `preflight=false → skipped` branch.

**Superseded runs.** A new push to the same PR cancels the superseded run
through the workflow `concurrency` group. CI Gate is `if: always()`, so it
still runs for that stale SHA and fails there (see the `concurrency` comment
in `ci.yml`). That red lands on a commit that is no longer the PR head. The
replacement run on the new head is the one that decides the PR.

## Fast checks (#8750 phase A.2)

Every `ci.yml` job runs on a GitHub-hosted runner, and the account runs at
most 20 jobs at once. Preflight, Ruff, Plan Validate and TypeSafe triage each
took about 1 to 3 minutes, and each held a full runner slot while pytest
shards waited for one. The `fast-checks` job (`needs: changes`) now runs them
as steps of one job: one checkout (full history), one `setup-python` with pip
cache, and uv plus the shard-style `.venv` install and Atlas hydrate only
when `preflight=true`. Ruff and Plan Validate install their own small pip
dependencies inside their steps. Four jobs became one, so every run holds
three fewer runner slots.

**Every check runs.** Each check step has `if: ${{ !cancelled() && <its
original job condition> }}`, so a failed step does not skip the checks after
it, and one run reports every red check. A cancelled run still skips them.
Preflight runs first, for the earliest signal.

**Timeouts.** Each check keeps its old job timeout as a step
`timeout-minutes`: Preflight 8, Ruff 5, Plan Validate 10, TypeSafe triage 5.
The job timeout is 35: the 28-minute sum plus 7 for checkout and the
preflight install.

**Outputs, not conclusions.** Each check step has an `id`, and the job
exposes `steps.<id>.outcome` as the outputs `preflight`, `ruff`,
`plan_validate` and `typesafe`. CI Gate reads those outcomes, never a step
`conclusion`: under `continue-on-error` a failed step concludes `success`.
A step skipped by its condition reports `skipped`.

**CI Gate rule for Fast checks:**

- The job result must be `success` or `failure`. `cancelled`, `skipped` or a
  missing result fails the gate.
- The Changes flags these rules read (`preflight`, `docs_only`) must be
  `true` or `false`; anything else fails the gate.
- Preflight: `success` when `preflight=true`, `skipped` otherwise.
- Ruff: `success` when `docs_only=false`, `skipped` otherwise.
- Plan Validate: always `success`.
- TypeSafe triage: logged, never blocks. A missing output still fails the gate,
  because it means the job outputs are broken.
- The gate logs every check's outcome before it fails, so one gate log names
  every red check.
- If every check passed its rule but the job still failed, a setup step
  (checkout, Python, the preflight install) broke, and the gate fails.

`tests/test_ci_pr_triggers.py` runs the real gate script for every
check × condition × outcome combination, including cancelled and missing
outputs.

**Retry trade-off.** "Re-run failed jobs" now re-runs all four checks, not
only the red one. A Ruff fix therefore costs up to one more Preflight run
(about 3 minutes). That is the price of freeing three runner slots per run.

## pytest shard collection and balance (ci-shard-balance-2026-09-07)

The code pytest shards run on all 4 runner vCPUs (`-n logical`, not `-n auto`
which counts physical cores), collect through one initial `tests` path
instead of positional file arguments, and balance by measured per-file
duration instead of a modulo split. Full-tier shard count (`10`) is declared
once in `ci.yml`'s workflow-level `env: PYTEST_SHARD_COUNT`. The Changes job
emits `shard_count` (1 or 10) and `shards`; `plan-files` always uses
`needs.changes.outputs.shard_count` so selected mode never LPT-partitions a
candidate set into unused buckets.
`--max-worker-restart=0` fails the job on a worker crash: pytest-timeout's
thread method terminates the process, and replacing it can leave xdist
hanging until the job limit.

Dispatch workers are a separate host from these runners. SCOPE for #8645
part B: this guards workers against accidental xdist fan-out and concurrent
full suites. It is not a sandbox against deliberate evasion; parts A (memory
admission) and C (per-worker cgroup) are the hard limits.

When `LEARN_UKRAINIAN_DISPATCH_TASK_ID` is set, `scripts/ci/pytest_dispatch_cap.py`
clamps xdist to two workers. `pyproject.toml` `addopts` still passes
`-p ci.pytest_dispatch_cap`, and `scripts/delegate.py` also sets
`PYTEST_PLUGINS=ci.pytest_dispatch_cap` (appended when the variable is already
set). `build_agent_env` forwards that variable into the agent CLI only while
the dispatch marker is set, and only as the single entry
`ci.pytest_dispatch_cap` — any other comma-separated plugin name is dropped.
A worker that copies CI's `--override-ini addopts=-v` therefore still loads
the cap. The `pythonpath` ini key is separate from `addopts` and still
makes `ci.pytest_dispatch_cap` importable. The plugin is idempotent when both
registrations load it. `-n auto`, `-n logical`, and an explicit `-n` use
`--maxprocesses=2`. A `--tx` spec whose expanded worker count is greater than
2 (for example `--tx 3*popen`) is a usage error before configuration; the cap
does not rewrite the spec. A full-suite invocation takes one non-blocking lock
under `/var/tmp/lu/learn-ukrainian/` (`LU_PYTEST_FULL_SUITE_LOCK` overrides
that path). The fd is stored on the pytest config that acquired it and
released only in that run's `pytest_unconfigure`, so a nested `pytest.main()`
does not drop the outer run's lock. CI does not set the dispatch variable
(see `.github/workflows/`), so shard `-n logical` is unchanged. A second
full-suite run on a dispatch host fails immediately and tells the worker to
run targeted tests.

**Collection — allowlist hook.** `tests/conftest.py` implements
`pytest_ignore_collect`, gated on env var `LU_PYTEST_SHARD_FILES`: unset,
collection is completely unchanged (local dev, `docs_skills` lane); set, it
must point at a readable, non-empty, newline-delimited list of repo-relative
`test_*.py` paths with no duplicates — anything else (missing, unreadable,
malformed, empty) raises loudly at first collection. Directories are never
filtered by the hook: it explicitly admits them and allowed files, overriding
pytest's default `norecursedirs` exclusions such as `build`; other files are
ignored. This preserves the tracked-file selection, including `tests/build/`.

**Balance — `scripts/ci/pytest_shards.py` file plane.** The file-plane subcommands,
extending the existing planner (Cursor Cloud's node-ID plane — `plan` /
`plan-shard` / `run` / `verify-artifacts` — is untouched):

- `plan-files --shard-id N --shard-count K --durations <json> --output <path>`:
  reads candidate repo-relative file paths from stdin (`ci.yml` pipes in
  `git ls-files -- tests | grep -E '/test_[^/]+\.py$' | sort`), LPT-assigns
  them across `K` shards from the run's frozen duration snapshot (median
  fallback for files without history), writes shard `N`'s sorted allowlist,
  and prints every shard's predicted weight.
- `file-durations --junit <xml>... --output <json>`: refreshes the committed
  snapshot from JUnit reports. Aggregation policy: a JUnit
  `<testcase time="...">` already sums setup+call+teardown for that node
  (pytest's own writer combines the three), so no phase decomposition is
  attempted; the same node ID appearing in more than one report (a rerun, or
  the same file spanning several reports) keeps the maximum, not the sum,
  before per-file totals are formed; a testcase whose `classname`/`name`
  doesn't resolve to a repo test file is skipped and counted, never raised.

**Duration source.** For a full-tier run, Changes searches recent successful
merge-queue runs for the newest complete pytest matrix. It requires all pytest
jobs and their matching JUnit artifacts, checks disjoint testcase identities,
rejects failures and reports with less than 90% of the committed file coverage,
and ignores runs older than seven days. It uploads one immutable duration file
for every shard of this CI run. An unavailable, incomplete, or stale source
selects `scripts/ci/pytest-file-durations.json` and logs why. Selected runs use
the committed file directly. CI Gate checks pytest shard completeness from
`needs` data alone, never a jobs-API re-listing (#8967: querying
`/actions/runs/{id}/attempts/{attempt}/jobs` right after `needs` resolved
sometimes returned an incomplete page — 10/10 shards green, Gate saw 6 and
failed). `needs.pytest.result` is GitHub's own aggregate over every matrix
instance from `fromJSON(needs.changes.outputs.shards)`, computed at
needs-resolution time, so it is success only when every shard concluded
success; the gate also cross-checks `needs.changes.outputs.shard_count`
against the length of that same `shards` array (both written by one
`classify_changes` call) so the two can never silently drift. A missing,
failed, or unexpectedly skipped shard still fails the required gate. The `needs_artifact`
skip-set audit runs as a parallel required job, so its collection and runtime
checks do not extend shard 1's pytest path.
Manual `workflow_dispatch` shard trials use a run-specific concurrency group;
pull-request cancellation and merge-group sequencing retain their existing keys.
Pytest jobs retain full checkout history because reviewer parity tests load
historical source with `git show`.

**Committed snapshot refresh procedure.** After a complete full merge-queue CI
run, download each shard's uploaded `pytest-junit-shard-N` artifact and run:

```
args=()
for shard in $(seq 1 10); do args+=(--junit "pytest-shard-${shard}.xml"); done
.venv/bin/python scripts/ci/pytest_shards.py file-durations \
  "${args[@]}" --output scripts/ci/pytest-file-durations.json
```

Use one `--junit` per shard in that run. Commit the refreshed snapshot (sorted
keys, 3-decimal rounding) when shard balance measurably drifts — not on every
green run.

## Cloud advisory runner dependency parity (#6977 slice A)

`scripts/ci/cursor_cloud_full_pytest.sh` (the offline-verifiable Cursor cloud
pytest prototype; see `docs/design/2026-09-06-cloud-agent-pytest-advisory.md`)
mirrors this job's "Install Python deps" and "Hydrate Atlas lexicon manifest"
steps: same lockfile exclude set (`torch`/`torchvision`/`open_clip_torch`/
`stanza`), `uv pip` when available, `packages/v4-runtime --no-build-isolation`
+ `build_assets.py`, and an unconditional hard-fail manifest hydrate. It also
requires `LEARN_UKRAINIAN_CP_PG_DSN` (same fixture creds as this job's
disposable Postgres service) whenever control-plane tests are selected, and
detects (never sudo-installs) the Linux native deps this job's "Install
native mechanism test dependencies" step provisions (`bubblewrap`, `libpq`).
**When this job's dependency install recipe changes, update the runner
script to match** — a drifted runner is a false-green risk, not just stale
docs (the whole point of that runner is offline/local sealed-run parity with
this job). Runner ↔ CI parity is covered offline by
`tests/ci/test_cursor_cloud_pytest_verify.py`; artifact transport, live cloud
qualification and the advisory Check publisher remain open (operator/advisor
GO required, see the design doc's "Explicit open decision" section).
