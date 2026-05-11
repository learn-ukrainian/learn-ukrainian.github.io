# Local CI Replay with `act`

> **TL;DR.** `scripts/local-ci.sh -W .github/workflows/ci.yml -j lint` runs
> the exact GHA workflow file locally in Docker via [act][act]. Same
> workflow file as production; no fork. First run pulls a ~1 GB runner
> image; subsequent runs reuse the container with `--reuse` so
> iteration drops to seconds for lightweight jobs.
>
> Tracked under GH issue [#1891][issue-1891]. Decision history: we chose
> `act` over Dagger after the orchestrator pushed back — Dagger requires
> rewriting all pipelines as Python/Go/TS code (months of work), while
> `act` replays the existing `.github/workflows/*.yml` unchanged.

[act]: https://github.com/nektos/act
[issue-1891]: https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1891

---

## Why this exists

The `Test (pytest)` GHA job takes ~4m17s end-to-end (cold setup-python,
fresh pip install of every requirement, full sources.db build). Locally
in `.venv/`, pytest discovery is ~0.19s. The 1300× gap is the dev-loop
tax we pay every time we have to debug something that only reproduces
on a GHA runner — typically the gnarliest CI bugs.

`act` closes the gap by running the same workflow YAML inside a
container that approximates the GHA runner. The first run is the
investment (image pull + dep install), every subsequent run is fast.

## Setup (one-time)

```bash
brew install act      # macOS host
```

You also need a running container daemon. The project assumes
**OrbStack** — `scripts/local-ci.sh` auto-resolves the OrbStack socket
at `~/.orbstack/run/docker.sock` and auto-starts the daemon if it's
not running. Docker Desktop also works; set `DOCKER_HOST` manually
(`unix:///var/run/docker.sock`) and skip the OrbStack auto-start logic
or replace it in the wrapper.

The repo already contains:

- **`.actrc`** — project defaults: Apple-Silicon arch pin
  (`--container-architecture linux/amd64`), runner image
  (`ghcr.io/catthehacker/ubuntu:act-latest`), `--rm`, `--reuse`.
- **`.github/act-event-push.json`** — static fallback event payload
  (used when git lookup fails inside the wrapper).
- **`scripts/local-ci.sh`** — thin wrapper that:
  1. starts OrbStack if needed,
  2. exports `DOCKER_HOST` to the OrbStack socket,
  3. templates a fresh push-event payload with real `before`/`after`
     SHAs from `git rev-parse` so `dorny/paths-filter@v4` (the gating
     action in `ci.yml::changes`) detects real changes,
  4. forwards every other flag verbatim to `act`.

## Common commands

```bash
# List discoverable jobs
scripts/local-ci.sh -l

# Validate a job without running it
scripts/local-ci.sh -W .github/workflows/ci.yml -j lint --dryrun

# Run one job
scripts/local-ci.sh -W .github/workflows/ci.yml -j lint
scripts/local-ci.sh -W .github/workflows/ci.yml -j test
scripts/local-ci.sh -W .github/workflows/ci.yml -j frontend

# Force a fresh container (no --reuse), useful when you need a true
# cold-start replay of the GHA path
scripts/local-ci.sh -W .github/workflows/ci.yml -j test --rm
```

## Measured timings (verified 2026-05-11)

### `Lint (ruff)` — lightweight job

| Run | Description | Real time |
|---|---|---|
| 1 (cold) | Fresh image pull + first run | ~42s (failed on event payload — pre-wrapper-fix) |
| 2 (image cached) | Image cached, container fresh | **64s** end-to-end |
| 3 (`--reuse`) | Same job, container reused, deps already installed | **38s** |

For comparison, the same `Lint (ruff)` job on GHA: ~25-35s plus queue
wait. Local with `--reuse` is comparable to GHA wall-clock with zero
queue wait.

### `Test (pytest)` — heavy job

| Run | Description | Real time |
|---|---|---|
| 1 (image cached, fresh container) | Full pip install + torch CPU wheel + pytest run | **7m45s** total — 4m41s in pytest proper |

GHA equivalent: ~4m17s. **`act` is slower than GHA on this heavy job**
because:
- QEMU emulating amd64 on Apple Silicon adds ~2-3× CPU overhead for
  CPU-bound steps (annotation, dictionary lookups, perf budgets).
- `actions/cache@v4` is a no-op under `act`, so pip wheels and the
  torch CPU wheel are downloaded fresh on every cold-container run.

`--reuse` should narrow the gap dramatically on the 2nd+ run (pip
"already satisfied" path) — pending follow-up measurement.

**Net value prop is NOT raw speed on heavy jobs.** It's:
1. **No GHA queue wait** — push → push → push iteration on a CI fix.
2. **Local debug access** — `docker exec` into the runner container,
   inspect file state, drop into a shell mid-run.
3. **CI-only failures reproduce locally** without polluting the PR
   with debugging commits.

For lightweight jobs (`lint`, `lint-prompts`, schema-check), `act` is
competitive with GHA wall-clock. For `Test (pytest)`, GHA wins on
raw time but `act` wins on iteration latency.

## Known failure modes under act (verified 2026-05-11)

When the full pytest suite runs via `act` on Apple Silicon, **7 of
7113 tests fail** — all explainable by the runner environment, not
by real bugs:

### `rsync: command not found` (4 failures)

`tests/test_deploy_script_idempotency.py` runs
`scripts/deploy_prompts.sh` and asserts return code 0. The script
uses `rsync` at line 205. `ghcr.io/catthehacker/ubuntu:act-latest`
**does not ship rsync** — GHA's `ubuntu-latest` does.

Workarounds:
- Switch to `ghcr.io/catthehacker/ubuntu:full-22.04` (~17 GB, ships
  rsync among many other tools). Heavy first download but works.
- Pre-install rsync via a custom `Dockerfile.act` (smaller image
  delta).
- Accept these 4 tests as `act`-incompatible and skip with
  `--deselect=tests/test_deploy_script_idempotency.py`.

### Perf-budget failures (3 failures)

Tests with hardcoded wall-clock budgets calibrated for native
amd64 fail under QEMU emulation:

- `test_annotation_speed` — 27s vs 15s budget (~1.8×)
- `test_playground_primary_endpoints_keep_health_fast` p95 — 1.72s vs 1.5s (~1.15×)
- `test_endpoint_performance_under_budget` — 909ms vs 500ms (~1.8×)

These pass on GHA. They fail under `act` purely because emulation is
slower. Mitigation: skip perf tests when running under act —
`-k "not perf and not speed and not budget"` or similar.

## Recommended `act` invocation pattern for pytest

To filter out the known failure modes above, run pytest jobs with:

```bash
scripts/local-ci.sh -W .github/workflows/ci.yml -j test
# Then expect:
#   - 6,966 pass
#   - 7 fail (4 rsync-missing + 3 perf-budget) — IGNORE these locally
#   - Real regressions: anything OUTSIDE those 7 known-act-failures
```

A cleaner long-term answer is to (a) install rsync in a custom act
image and (b) tag the perf tests so they auto-skip under
`ACT_LOCAL_REPLAY=1`. Tracked as follow-up to #1891.

## Known gotchas

### `dorny/paths-filter@v4` needs `repository.default_branch`

`act` synthesizes a minimal event payload that omits
`repository.default_branch`. The `changes` job in `ci.yml` uses
`dorny/paths-filter@v4` to decide which downstream jobs run; without
the field, the action errors out with:

> Error: This action requires 'base' input to be configured or
> 'repository.default_branch' to be set in the event payload

The wrapper script handles this by templating a richer event payload
on every invocation. If you call `act` directly, pass
`--eventpath .github/act-event-push.json` or accept that gated jobs
will fail their `needs:` step.

### `before`/`after` SHAs must produce a real diff

Path-filter compares files changed between `before` and `after`. If
both are `0000...0000`, no files appear changed, and every job gated
on `needs.changes.outputs.code == 'true'` skips its inner steps (the
job itself still passes — that's how the production CI satisfies its
required check on docs-only PRs). The wrapper sets `before = HEAD~1`
and `after = HEAD` so the most recent commit's changes register.

### `actions/cache@v4` is a no-op

`act` does not implement GHA's hosted cache. The `cache: 'pip'`
parameter on `actions/setup-python` quietly does nothing. Mitigation:

- `--reuse` in `.actrc` keeps the same container across invocations,
  so pip's local install survives between runs.
- The first run still pays the full install cost; that's the
  one-time investment.

### Heavy native deps re-download every fresh-image run

`requirements-lock.txt` includes `torch==2.11.0` (~600 MB CPU wheel),
`pyarrow`, `lxml`, etc. With `--reuse`, the second run skips re-install
because pip sees "already satisfied." Without `--reuse`, every run
re-downloads everything. Stick with `--reuse` for iteration; pass
`--rm` only when you specifically need a cold-start replay.

### Apple Silicon emulation overhead

We pin `--container-architecture linux/amd64` to match GHA runners.
QEMU emulation on arm64 hosts makes CPU-heavy steps ~2-3× slower than
they'd be on a native amd64 host. For pure I/O and pip install this is
invisible; for pytest collection on a large test suite it adds 10-20s.

### Gemini-Dispatch workflows don't replay locally

`gemini-*.yml` workflows need `secrets.GEMINI_API_KEY` and OIDC tokens
that don't exist on a local runner. Don't try to `act` them; their
local equivalent is the regular `gemini` CLI or `ab ask-gemini`.

## When NOT to use `act`

- **You just want to run pytest on the actual code.** Use
  `.venv/bin/python -m pytest tests/` — it's 0.19s for discovery,
  seconds for the suite. `act` is for testing the GHA workflow
  configuration itself, not the application code.
- **You're debugging a Gemini-Dispatch (GHA-only) workflow.** Those
  need GHA secrets `act` can't provide. Test by pushing a draft PR.
- **You don't have Docker available** (corporate-locked laptop, etc).
  Without a container daemon, `act` can't run anything.

## Lifting this pattern to another project

Per the design goal of #1891 (callable from any project):

1. Copy `.actrc`, `scripts/local-ci.sh`, and
   `.github/act-event-push.json` into the target project.
2. Adjust `.actrc` runner images if the project uses non-Ubuntu
   runners or specific Ubuntu versions.
3. Adjust the static event JSON's `repository.full_name` and `owner`
   to match the target project (the wrapper-templated version uses
   them but the static fallback hardcodes ours).
4. Replace the OrbStack-specific lines in `scripts/local-ci.sh` if
   you're on Docker Desktop or another daemon — see the comment block
   at the top of the wrapper.

The repo-local install pattern (per-project `scripts/` wrapper) was
chosen over a global tool because:

- Each project's runner-image / arch / event-payload requirements
  differ; baking them into `.actrc` keeps them versioned with the
  project.
- The wrapper code is short (~50 lines) and self-explanatory; no
  install ceremony.
- A global `~/.dotfiles`-style install would couple the user's setup
  to one specific daemon (OrbStack), losing portability for
  collaborators on Docker Desktop.
