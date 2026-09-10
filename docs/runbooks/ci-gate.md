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
| pytest | always (`full` → 4 shards; `selected` → 1 shard over candidates; `docs` → 1 `docs_skills` shard) |
| Contracts | not docs-only |
| Frontend | when frontend paths changed |
| CI Gate | always |

The Changes job uses `scripts/ci/classify_changes.py`. Ordinary PRs skip
ruff/contracts and run one `docs_skills` pytest leg only when every path is
Markdown in docs/, shared skills, agent deploy trees, or the repository root,
or belongs to wiki/ or curriculum/ (owned by Content CI). Frontend denominator
matches always override the docs exemption, including `packages/activity-kit/`.
Unknown paths, including Markdown under unrecognized or executable trees, run
the full pytest shard set and ruff/contracts; frontend follows its denominator.
All docs YAML, schemas, packages, dashboards, dependency manifests/locks,
Python/pre-commit configuration, and scripts/config or scripts/ci changes
therefore run the full PR-tier floor.

Merge groups force the full tier, including frontend. Previously they used the
same path classifier as PRs and could run only the docs selection. A PR carrying
`full-ci` also forces the full tier; adding a label triggers a fresh run.
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
