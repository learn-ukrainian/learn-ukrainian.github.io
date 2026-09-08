# CI Gate

New workflow (Fable 5.1, 2026-09-03). `.github/workflows/ci.yml` is a short
replacement, not the old two-tier merge-queue file.

`CI Gate` is the only required GitHub check. Same jobs on `pull_request` and
`merge_group`.

| Job | When |
| --- | --- |
| Changes | always (GitHub compare API; `docs_only` / `frontend` / `shards`) |
| Ruff | not docs-only |
| Secret scan | always |
| pytest | always (4 shards for code, 1 `docs_skills` shard for docs/skills) |
| Contracts | not docs-only |
| Frontend | when frontend paths changed |
| CI Gate | always |

Docs/skills PRs (every changed path is docs/, shared skills, agent deploy
trees, or `*.md`) skip ruff/contracts/frontend and run one pytest leg with
`-m docs_skills`. Compare API failure fail-closes to a full code run.

No CF attest. No auto-arm. No landing-class classifier. No coverage floor.
Red team review is out of band.

## pytest shard collection and balance (ci-shard-balance-2026-09-07)

The code pytest shards run on all 4 runner vCPUs (`-n logical`, not `-n auto`
which counts physical cores), collect through one initial `tests` path
instead of positional file arguments, and balance by measured per-file
duration instead of a modulo split. Shard count (`4`) is declared once in
`ci.yml`'s workflow-level `env: PYTEST_SHARD_COUNT`, read by both the
`changes` job's `shards` output and the pytest job's `plan-files` call.

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
