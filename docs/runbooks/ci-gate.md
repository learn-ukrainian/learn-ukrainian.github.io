# CI Gate

New workflow (Fable 5.1, 2026-09-03). `.github/workflows/ci.yml` is a short
replacement, not the old two-tier merge-queue file.

`CI Gate` is the only required GitHub check. Same jobs on `pull_request` and
`merge_group`.

| Job | When |
| --- | --- |
| Changes | always (`docs_only` / `frontend` / `shards` / `pytest_mode` / `shard_count` / `pytest_candidates`) |
| Ruff | not docs-only |
| Secret scan | always |
| pytest | always (`full` → 4 shards; `selected` → 1 shard over candidates plus the `repo_wide` tests; `docs` → 1 `docs_skills` shard plus the `repo_wide` tests; `content` → 1 shard: `-m 'reads_content and not slow and not atlas_release'` `--timeout=120` + shard safety net) |
| Contracts | not docs-only |
| Frontend | when frontend paths changed (always on for the content class: content renders through the site build) |
| TypeSafe triage | always (advisory during soak, #8232: CI Gate accepts success/skipped/**failure**, so a red TypeSafe check is visible but does not fail the gate. Missing `TYPESAFE_API_KEY`, API/transport errors and malformed responses skip green; only a `broken` verdict with choice confidence or `high_risk` >= 0.8 turns the job red) |
| CI Gate | always |

The Changes job uses `scripts/ci/classify_changes.py`. Ordinary PRs skip
ruff/contracts and run one `docs_skills` pytest leg only when every path is
Markdown in docs/, shared skills, agent deploy trees, or the repository root,
or belongs to curriculum/ or wiki/ without a `site/` path (the curriculum/wiki
fast path predates the content class; the queue run is its safety net).
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
- **merge_group**: classified with the same path classes as a PR, using each
  queue entry's own changed paths (ALLGREEN), so a group can resolve to any
  tier. Any lookup failure or ambiguity resolves to `full`.

The content class emits `pytest_mode=content`: one shard running
`-m 'reads_content and not slow and not atlas_release'` (same filters and
`--timeout=120` as the full PR tier) plus `tests/test_ci_shard_partition.py`,
with Ruff, Contracts and the Frontend build still on (`docs_only=false`,
`frontend=true`). The marker is load-bearing:
`tests/test_reads_content_marker_invariant.py` fails when a test module
references those content roots without carrying `reads_content`, so new
content-reading tests cannot silently fall out of the class.

CI runs on `pull_request` opened/synchronize/reopened; labels and PR-body
edits do not start it. `full-ci` is read from the PR's current labels
(case-insensitive, fail closed) on the next PR push and in every merge-queue
run, where every PR in the group is resolved from the queue refs. A label added
after a green PR run does not rerun it: push again, or rely on the merge queue.
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
`pytest_mode=full` with four shards. Contracts and ruff stay on whenever
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

The **content lane** is deliberately unchanged. Every repo-wide test that reads
a content tree also carries `reads_content`, so `-m 'reads_content and not slow
and not atlas_release'` already runs it: `tests/test_llm_reviewer_dispatch.py`,
`tests/test_threshold_source_of_truth.py`, `tests/test_sparse_collection_guard.py`,
`tests/test_public_tree_no_baked_host_run_root.py`,
`tests/api/test_app_factory.py`, and
`tests/test_curriculum_upgrade_no_host_run_root.py` are all marked both ways,
and none is `slow`/`atlas_release`.

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

## pytest shard collection and balance (ci-shard-balance-2026-09-07)

The code pytest shards run on all 4 runner vCPUs (`-n logical`, not `-n auto`
which counts physical cores), collect through one initial `tests` path
instead of positional file arguments, and balance by measured per-file
duration instead of a modulo split. Full-tier shard count (`4`) is declared
once in `ci.yml`'s workflow-level `env: PYTEST_SHARD_COUNT`. The Changes job
emits `shard_count` (1 or 4) and `shards`; `plan-files` always uses
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

**Balance — `scripts/ci/pytest_shards.py` file plane.** Two new subcommands,
extending the existing planner (Cursor Cloud's node-ID plane — `plan` /
`plan-shard` / `run` / `verify-artifacts` — is untouched):

- `plan-files --shard-id N --shard-count K --durations <json> --output <path>`:
  reads candidate repo-relative file paths from stdin (`ci.yml` pipes in
  `git ls-files -- tests | grep -E '/test_[^/]+\.py$' | sort`), LPT-assigns
  them across `K` shards from the committed duration snapshot (median
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

**Snapshot refresh procedure.** After a landing-tier CI run (`merge_group` or
`push` to `main`), download each shard's uploaded `pytest-junit-shard-N`
artifact and run:

```
.venv/bin/python scripts/ci/pytest_shards.py file-durations \
  --junit pytest-shard-1.xml --junit pytest-shard-2.xml \
  --junit pytest-shard-3.xml --junit pytest-shard-4.xml \
  --output scripts/ci/pytest-file-durations.json
```

Commit the refreshed snapshot (sorted keys, 3-decimal rounding) when shard
balance measurably drifts — not on every green run.

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
